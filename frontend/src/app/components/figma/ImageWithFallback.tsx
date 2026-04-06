import React, { useState, useEffect } from 'react'

const ERROR_IMG_SRC =
  'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODgiIGhlaWdodD0iODgiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgc3Ryb2tlPSIjMDAwIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBvcGFjaXR5PSIuMyIgZmlsbD0ibm9uZSIgc3Ryb2tlLXdpZHRoPSIzLjciPjxyZWN0IHg9IjE2IiB5PSIxNiIgd2lkdGg9IjU2IiBoZWlnaHQ9IjU2IiByeD0iNiIvPjxwYXRoIGQ9Im0xNiA1OCAxNi0xOCAzMiAzMiIvPjxjaXJjbGUgY3g9IjUzIiBjeT0iMzUiIHI9IjciLz48L3N2Zz4KCg=='

/** Builds the list of URLs to try in order: original, then the other extension. */
function buildSrcQueue(src: string | undefined): string[] {
  if (!src) return []
  if (src.endsWith('.png')) return [src, src.replace('.png', '.jpg')]
  if (src.endsWith('.jpg')) return [src, src.replace('.jpg', '.png')]
  if (src.endsWith('.jpeg')) return [src, src.replace('.jpeg', '.png')]
  // No recognised extension — just try as-is
  return [src]
}

export function ImageWithFallback(props: React.ImgHTMLAttributes<HTMLImageElement>) {
  const { src, alt, style, className, ...rest } = props

  const [queue, setQueue] = useState<string[]>(() => buildSrcQueue(src as string | undefined))
  const [idx, setIdx] = useState(0)
  const [didError, setDidError] = useState(false)

  // Reset when the src prop changes (e.g. different venue selected)
  useEffect(() => {
    const q = buildSrcQueue(src as string | undefined)
    setQueue(q)
    setIdx(0)
    setDidError(false)
  }, [src])

  const handleError = () => {
    const nextIdx = idx + 1
    if (nextIdx < queue.length) {
      // Try the next URL in the queue (e.g. .jpg after .png failed)
      setIdx(nextIdx)
    } else {
      // All options exhausted
      setDidError(true)
    }
  }

  if (!src || didError) {
    return (
      <div
        className={`inline-block bg-gray-800 text-center align-middle ${className ?? ''}`}
        style={style}
      >
        <div className="flex items-center justify-center w-full h-full">
          <img src={ERROR_IMG_SRC} alt="Error loading image" {...rest} data-original-url={src} />
        </div>
      </div>
    )
  }

  return (
    <img
      src={queue[idx]}
      alt={alt}
      className={className}
      style={style}
      {...rest}
      onError={handleError}
    />
  )
}
