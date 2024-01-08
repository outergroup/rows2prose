export * from "./src/visual";

const numberArrayClasses = {
  "float32": Float32Array,
  "float64": Float64Array,
  "uint32": Uint32Array,
  "int32": Int32Array,
  "uint64": BigUint64Array,
  "int64": BigInt64Array
};

function parseColumns(d) {
  let parsed = {};
  Object.keys(d).forEach(k => {
    const type = d[k].type,
          buffer = Uint8Array.from(atob(d[k].data), c => c.charCodeAt(0)).buffer;
    if (!(type in numberArrayClasses)) {
      throw new Error(`Unknown data type: ${type}`);
    }
    parsed[k] = new numberArrayClasses[type](buffer);
  });
  return parsed;
}

export {parseColumns};
