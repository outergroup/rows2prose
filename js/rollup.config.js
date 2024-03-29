import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';

const commonPlugins = [
  resolve(),
  commonjs(),
];

export default [
  // Existing library configuration
  {
    input: 'index.js',
    output: [
      {
        file: 'dist/rows2prose.esm.js',
        format: 'esm',
        sourcemap: true
      },
      {
        file: 'dist/rows2prose.browser.js',
        format: 'iife',
        name: 'r2p', // This will be the global variable name in the browser
        sourcemap: true
      }
    ],
    plugins: commonPlugins
  },
];
