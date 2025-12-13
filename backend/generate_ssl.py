"""
Genera un certificado SSL autofirmado para el servidor HTTPS.
Solo necesita ejecutarse una vez.
"""
import os
from datetime import datetime, timedelta

def generate_ssl_certificate():
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    
    ssl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ssl")
    key_path = os.path.join(ssl_dir, "key.pem")
    cert_path = os.path.join(ssl_dir, "cert.pem")
    
    # Crear carpeta ssl si no existe
    os.makedirs(ssl_dir, exist_ok=True)
    
    # Si ya existen, no regenerar
    if os.path.exists(key_path) and os.path.exists(cert_path):
        print("Certificado SSL ya existe.")
        return key_path, cert_path
    
    print("Generando certificado SSL autofirmado...")
    
    # Generar clave privada
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Crear certificado
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "AR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Scanner Pipos"),
        x509.NameAttribute(NameOID.COMMON_NAME, "scanner-pipos.local"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365 * 10)  # 10 años
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("*.local"),
            x509.IPAddress(__import__('ipaddress').IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    ).sign(key, hashes.SHA256(), default_backend())
    
    # Guardar clave privada
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Guardar certificado
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print(f"Certificado generado: {cert_path}")
    return key_path, cert_path


if __name__ == "__main__":
    generate_ssl_certificate()
