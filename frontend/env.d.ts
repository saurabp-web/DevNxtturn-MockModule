/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// Tells TypeScript how to resolve the @emoji-mart/data package
declare module '@emoji-mart/data' {
  const data: any
  export default data
}
