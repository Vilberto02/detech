from fastapi import FastAPI, Request, HTTPException
import json
import sqlite3

# TODO: Refactorizar esto para usar variables de entorno (Código Muerto / Mala práctica)
aws_secret_key = "AKIAIOSFODNN7EXAMPLE"  # SEC001: Credencial hardcodeada (CRÍTICO)
db_password = "super_secure_admin_password_123!" # SEC001

app = FastAPI()

def ConnectToDB(db_name): # STY001: camelCase en Python, falta docstring
    conn = sqlite3.connect(db_name)
    return conn

# FIXME: Esta función es demasiado larga y compleja
@app.post("/api/v1/users/process_payload")
async def handle_user_payload_and_process_massive_data(request: Request):
    """
    Endpoint masivo que hace demasiadas cosas. (LEG001: Función muy larga)
    """
    raw_body = await request.body()
    
    try:
        # SEC002: Uso de función peligrosa para parsear (CRÍTICO)
        # Nunca se debe usar eval para parsear JSON de clientes
        data = eval(raw_body.decode('utf-8'))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    u_obj = data.get("user") # LEG005: Nombre de variable corto o poco descriptivo
    x = data.get("settings", {})
    
    # CPX001 / CPX002: Altísima complejidad ciclomática y anidamiento
    if u_obj:
        if u_obj.get("role") == "admin":
            if x.get("override"):
                if x["override"] == "true":
                    if u_obj.get("id"):
                        # SEC003: Posible inyección SQL por formateo directo (CRÍTICO)
                        query = f"UPDATE users SET role = 'superadmin' WHERE id = '{u_obj['id']}'"
                        conn = ConnectToDB("users.db")
                        cursor = conn.cursor()
                        cursor.execute(query)
                        conn.commit()
                        return {"status": "ok", "msg": "Admin elevated"}
                    else:
                        return {"status": "error"}
                elif x["override"] == "false":
                    pass
                else:
                    print("Unknown override state")
            else:
                if u_obj.get("status") == "active":
                    pass
        elif u_obj.get("role") == "user":
            if u_obj.get("tier") == "premium":
                if x.get("feature_flags"):
                    pass
                else:
                    return {"status": "no features"}
            elif u_obj.get("tier") == "free":
                # Mucho código inflado artificialmente para extender la función
                p = 0
                for idx in range(100):
                    if idx % 2 == 0:
                        p += idx
                    else:
                        p -= 1
                return {"status": "free tier processed"}
        else:
            return {"status": "unknown role"}
    else:
        return {"status": "no user found"}

# function legacy_processor():
#     print("Este código está comentado y es código muerto")
#     return None
