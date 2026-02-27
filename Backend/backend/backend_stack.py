from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_rds as rds,
    Duration,
    aws_ecr_assets as ecr_assets,
)
from aws_cdk import aws_apprunner_alpha as apprunner
from constructs import Construct

class BackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ----------------------------------------------------------------
        # 1. Look up the Default VPC
        # ----------------------------------------------------------------
        vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

        # ----------------------------------------------------------------
        # 2. Add Security Group for our existing RDS instance 
        #    (Assuming it's using the default SG or you allow inbound 5432)
        # ----------------------------------------------------------------
        # We create a new Security Group for AppRunner/Lambda to access RDS
        db_client_sg = ec2.SecurityGroup(
            self, "DBClientSG",
            vpc=vpc,
            description="Security group for resources needing access to RDS",
            allow_all_outbound=True
        )
    
        # ----------------------------------------------------------------
        # 2b. Add an Ingress Rule to the RDS Security Group
        #     This allows Lambda/AppRunner to connect to the DB
        # ----------------------------------------------------------------
        # This is the default security group ID for your RDS instance
        rds_sg = ec2.SecurityGroup.from_security_group_id(self, "RDSSG", "sg-08c29b4e6734cadcc")
        rds_sg.add_ingress_rule(
            peer=db_client_sg,
            connection=ec2.Port.tcp(5432),
            description="Allow Postgres traffic from AppRunner and DBInitLambda"
        )

        # ----------------------------------------------------------------
        # 3. Create the Database Initialization Lambda Function
        #    This will run inside the VPC so it can hit the private DB
        # ----------------------------------------------------------------
        db_init_lambda = _lambda.Function(
            self, "DBInitLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="init_db.handler",
            code=_lambda.Code.from_asset("api/db_init"),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC), # Using public subnets in default VPC
            allow_public_subnet=True,
            security_groups=[db_client_sg],
            timeout=Duration.seconds(30),
            environment={
                # We will set these via AWS Console manually later, or pass them in here
                "DB_HOST": "database-1.c36wyoowwijy.us-east-2.rds.amazonaws.com",
                "DB_PORT": "5432",
                "DB_USER": "postgres",
                "DB_PASSWORD": "12345678",
                "DB_NAME": "postgres"
            }
        )

        # ----------------------------------------------------------------
        # 4. App Runner Service (Your FastAPI Application)
        # ----------------------------------------------------------------
        # Build the Docker image from our local api/ folder
        image_asset = ecr_assets.DockerImageAsset(
            self, "FastAPIImage",
            directory="api"
        )

        # App Runner instance role
        instance_role = iam.Role(
            self, "AppRunnerInstanceRole",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com")
        )

        # VPC Connector so AppRunner can reach RDS in the VPC
        vpc_connector = apprunner.VpcConnector(
            self, "AppRunnerVpcConnector",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[db_client_sg]
        )

        # The actual App Runner Service
        apprunner_service = apprunner.Service(
            self, "FastAPIService",
            source=apprunner.Source.from_asset(
                asset=image_asset,
                image_configuration=apprunner.ImageConfiguration(
                    port=8000,
                    environment_variables={
                        "DATABASE_URL": "postgresql://postgres:12345678@database-1.c36wyoowwijy.us-east-2.rds.amazonaws.com:5432/postgres"
                    }
                )
            ),
            instance_role=instance_role,
            vpc_connector=vpc_connector
        )
