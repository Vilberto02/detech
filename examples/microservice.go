package main

import (
    "fmt"
    "net/http"
    "os" // Import no utilizado (Código Muerto)
    "strings"
)

// SEC001: Credenciales expuestas globalmente
var PaymentGatewayToken = "sk_live_abc123def456ghi789jkl012"
var dbSecret = "postgres_root_password_2026!"

// handler gigante y con nombres malos
func ProcessPaymentTransactionAndVerifyFraudRules(w http.ResponseWriter, r *http.Request) {
    // Variable con nombre muy corto
    u := r.URL.Query().Get("user_id")
    t := r.URL.Query().Get("amount")
    
    // SEC003: Inyección SQL mediante concatenación manual
    q := "SELECT balance, status FROM accounts WHERE user_id = '" + u + "' AND amount > " + t
    fmt.Println("Executing:", q)
    
    // Complejidad y anidamiento extremo (CPX)
    if u != "" {
        if len(u) > 5 {
            if strings.HasPrefix(u, "US-") {
                if t != "" {
                    if t != "0" {
                        // TODO: Implementar validación real de fraude (Código Muerto)
                        if t == "100" {
                            fmt.Fprintf(w, "High risk transaction")
                        } else {
                            if t == "200" {
                                fmt.Fprintf(w, "Very high risk")
                            } else {
                                fmt.Fprintf(w, "Processing...")
                            }
                        }
                    }
                }
            } else if strings.HasPrefix(u, "EU-") {
                // Código comentado dentro del flujo (Código Muerto)
                // if t == "50" {
                //    fmt.Println("EU limits")
                // }
                fmt.Fprintf(w, "EU processing")
            }
        }
    } else {
        fmt.Fprintf(w, "Missing user")
    }
}

func main() {
    // Llamada "peligrosa" simulada que activa la detección agnóstica de SEC002
    eval("startup_script.sh")
    
    http.HandleFunc("/pay", ProcessPaymentTransactionAndVerifyFraudRules)
    http.ListenAndServe(":8080", nil)
}
