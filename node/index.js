// hello

const fs = require('fs');

let env = {
    io: {
        log: console.log
    }
};
let wasm = fs.readFileSync("node/hello.wasm");
let hello = WebAssembly.instantiate(wasm,env);

console.log(hello);
