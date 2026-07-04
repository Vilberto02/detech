package main

import (
    "fmt"
    "os"
)

// SEC001: Credenciales hardcodeadas (CRÍTICO)
var token = "ghp_1234567890abcdefGHIJKLMNOPQRSTUVWXYZ"
var private_key = "BEGIN RSA PRIVATE KEY..."

func main() {
    x := 10
    if x > 5 {
        fmt.Println("Mayor a 5")
    } else {
        fmt.Println("Menor o igual a 5")
    }
    
    // SEC003: Inyección SQL (CRÍTICO)
    userInput := "admin"
    query := "SELECT * FROM users WHERE username = '" + userInput + "'"
    fmt.Println(query)
    
    processData(x)
}

// camelCase en Go (Estilo)
func processData(val int) {
    // SEC002: Simulación de uso de eval, en Go no existe nativo pero se detecta por nombre
    eval("x = 10")
    
    for i := 0; i < val; i++ {
        if i%2 == 0 {
            fmt.Println(i)
        }
    }
}
