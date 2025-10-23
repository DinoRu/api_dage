"""CLI script to create admin user."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import AsyncSessionLocal
from app.services.auth import auth_service


async def create_admin():
    """Create admin user interactively."""
    print("\n" + "="*50)
    print("  CRÉATION D'UN ADMINISTRATEUR")
    print("="*50 + "\n")
    
    # Get input
    username = input("Nom d'utilisateur: ").strip()
    if not username:
        print("❌ Le nom d'utilisateur est requis")
        return
    
    full_name = input("Nom complet: ").strip()
    if not full_name:
        print("❌ Le nom complet est requis")
        return
    
    from getpass import getpass
    password = getpass("Mot de passe: ")
    if len(password) < 8:
        print("❌ Le mot de passe doit contenir au moins 8 caractères")
        return
    
    password_confirm = getpass("Confirmer le mot de passe: ")
    if password != password_confirm:
        print("❌ Les mots de passe ne correspondent pas")
        return
    
    # Create admin
    print("\n🔄 Création de l'administrateur...")
    
    async with AsyncSessionLocal() as db:
        try:
            admin = await auth_service.create_superuser(
                db,
                username=username,
                password=password,
                full_name=full_name
            )
            
            print(f"\n✅ Administrateur créé avec succès!")
            print(f"   ID: {admin.id}")
            print(f"   Username: {admin.username}")
            print(f"   Nom: {admin.full_name}")
            print(f"   Rôle: {admin.role}")
            
        except Exception as e:
            print(f"\n❌ Erreur: {str(e)}")


if __name__ == "__main__":
    asyncio.run(create_admin())