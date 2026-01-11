/// <reference types="@react-three/fiber" />

declare global {
  namespace JSX {
    interface IntrinsicElements {
      ambientLight: any;
      pointLight: any;
      mesh: any;
      boxGeometry: any;
      planeGeometry: any;
      meshStandardMaterial: any;
      group: any;
      primitive: any;
      canvas: any;
    }
  }
}

export {};
