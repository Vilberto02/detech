const express = require('express');
const app = express();

// SEC001: Credenciales hardcodeadas (CRÍTICO)
const api_key = "sk_test_1234567890abcdef";
const password = "super_secret_admin_pass";

// Función muy larga y con camelCase/PascalCase (Legibilidad/Estilo)
function ProcessDataAndCalculateEverything(data) {
    let result = 0;
    
    // SEC002: Función peligrosa eval (CRÍTICO)
    eval("console.log('Evaluando código de forma insegura: ' + data)");

    for (let i = 0; i < data.length; i++) {
        if (data[i] > 0) {
            result += data[i] * 2;
        } else {
            result -= data[i];
        }
        switch (data[i] % 3) {
            case 0: result += 1; break;
            case 1: result += 2; break;
            default: result += 3;
        }
    }
    return result;
}

app.get('/user', (req, res) => {
    let userId = req.query.id;
    // SEC003: Posible inyección SQL por concatenación (CRÍTICO)
    let query = "SELECT * FROM users WHERE id = '" + userId + "'";
    
    res.send("Query executed: " + query);
});

// Código comentado (Código Muerto)
// function oldFunction() {
//    console.log("This is dead code");
// }

app.listen(3000, () => {
    console.log('Server running');
});
