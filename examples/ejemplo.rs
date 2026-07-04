use std::collections::HashMap;
use std::fs::File;

// camelCase en Rust que usa snake_case (Estilo)
fn processData() {
    let mut x = HashMap::new(); // Nombre corto (Legibilidad)
    
    // SEC001: Credenciales hardcodeadas (CRÍTICO)
    let secret = "super_secret_token_123";
    let auth_token = "ey...jwt...token";
    
    x.insert("clave", "valor");
    
    // SEC003: Posible inyección SQL (CRÍTICO)
    let input = "1 OR 1=1";
    let query = "SELECT * FROM admins WHERE id = " + input;
    
    for (k, v) in &x {
        if k == &"clave" {
            println!("{}", v);
        } else {
            println!("No encontrado");
        }
    }
    
    // SEC002: Detecta función peligrosa por nombre
    eval("execute_something()");
}

fn main() {
    processData();
}
