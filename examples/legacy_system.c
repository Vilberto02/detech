#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// SEC001: Tokens y contraseñas hardcodeadas en variables globales
const char* api_key = "AIzaSyD-xxx_yyy_zzz_123456789";
const char* master_passwd = "admin_super_secret_pwd!";

// TODO: Refactorizar esta funcion gigante a modulos mas pequeños
void ProcessIncomingLegacyDataStream(char* buffer, int len) {
    int x = 0; // Variable muy corta
    char query[512];
    
    // SEC003: Posible SQL Injection formateado (%\s*\w en DETECH)
    sprintf(query, "SELECT * FROM legacy_users WHERE session_id = '%s'", buffer);
    printf("Debug: %s\n", query);
    
    // SEC002: Llamada peligrosa que puede ejecutar comandos de sistema
    // El analizador detectará "exec"
    exec("chmod +x temp.sh");
    
    // Altisima complejidad ciclomática
    for (int i = 0; i < len; i++) {
        if (buffer[i] == 'A') {
            if (i > 10) {
                if (buffer[i-1] == 'B') {
                    if (x == 0) {
                        x = 1;
                    } else if (x == 1) {
                        x = 2;
                    } else {
                        x = 0;
                    }
                } else {
                    x = -1;
                }
            }
        } else if (buffer[i] == 'C') {
            switch(x) {
                case 1:
                    printf("State 1\n");
                    break;
                case 2:
                    if (len > 50) {
                        printf("Large C block\n");
                    }
                    break;
                default:
                    printf("Unknown\n");
            }
        }
    }
    
    /*
    // Este es un bloque de código muerto gigante (DCO)
    void deprecated_logic() {
        int y = 0;
        y++;
        printf("Old logic");
    }
    */
}

int main(int argc, char** argv) {
    if (argc > 1) {
        ProcessIncomingLegacyDataStream(argv[1], strlen(argv[1]));
    }
    return 0;
}
