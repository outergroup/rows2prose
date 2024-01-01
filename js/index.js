export * from "./src/visual";

function parseColumns(d) {
  let parsed = {};
  Object.keys(d).forEach(k => {
    let type = d[k].type,
        data = d[k].data;
    if (type == "float32") {
      parsed[k] = new Float32Array(Uint8Array.from(atob(data), c => c.charCodeAt(0)).buffer);
    } else if (type == "float64") {
      parsed[k] = new Float64Array(Uint8Array.from(atob(data), c => c.charCodeAt(0)).buffer);
    } else if (type == "uint32") {
      parsed[k] = new Uint32Array(Uint8Array.from(atob(data), c => c.charCodeAt(0)).buffer);
    } else if (type == "int32") {
      parsed[k] = new Int32Array(Uint8Array.from(atob(data), c => c.charCodeAt(0)).buffer);
    } else {
      throw new Error(`Unknown data type: ${type}`);
    }
  });
  return parsed;
}

export {parseColumns};
