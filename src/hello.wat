;; <watfile:hello.wat>
;; https://www.youtube.com/watch?v=ojYEfRye6aE

(module
    (func $square (param i32) (result i32)
        local.get 0
        local.get 0
        i32.mul
    )
    (export "square" (func $square))

    (func (export "double") (param i32) (result i32)
        (i32.add (local.get 0)(local.get 0))
    )
)
