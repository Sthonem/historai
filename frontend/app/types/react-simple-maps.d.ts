declare module 'react-simple-maps' {
  import type { ComponentType, CSSProperties, ReactNode } from 'react'

  export interface Geography {
    rsmKey: string
    properties: Record<string, unknown> & { name: string }
  }

  export interface GeographiesChildrenArgs {
    geographies: Geography[]
    outline: ReactNode
    borders: ReactNode
  }

  export interface ComposableMapProps {
    projection?: string
    projectionConfig?: Record<string, unknown>
    width?: number
    height?: number
    style?: CSSProperties
    children?: ReactNode
  }

  export interface GeographiesProps {
    geography: string | object
    children: (args: GeographiesChildrenArgs) => ReactNode
  }

  export interface GeographyProps {
    geography: Geography
    fill?: string
    stroke?: string
    strokeWidth?: number
    style?: {
      default?: CSSProperties
      hover?: CSSProperties
      pressed?: CSSProperties
    }
  }

  export const ComposableMap: ComponentType<ComposableMapProps>
  export const Geographies: ComponentType<GeographiesProps>
  export const Geography: ComponentType<GeographyProps>
}
