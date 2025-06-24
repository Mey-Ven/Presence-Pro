#!/usr/bin/env python3
"""
Test simple du streaming web
"""

import requests
import time

def test_web_streaming():
    """Test du streaming web via l'interface"""
    print("🌐 TEST STREAMING WEB")
    print("=" * 40)
    
    session = requests.Session()
    
    try:
        # 1. Connexion admin
        print("🔐 Connexion admin...")
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post("http://localhost:5002/login", data=login_data)
        
        if response.status_code not in [200, 302]:
            print(f"❌ Connexion échouée: {response.status_code}")
            return False
        
        print("✅ Connexion réussie")
        
        # 2. Accès à la page de reconnaissance
        print("📄 Accès page reconnaissance...")
        response = session.get("http://localhost:5002/facial/recognition")
        
        if response.status_code != 200:
            print(f"❌ Page inaccessible: {response.status_code}")
            return False
        
        print("✅ Page accessible")
        
        # 3. Test de l'API de statut
        print("📊 Test API statut...")
        response = session.get("http://localhost:5002/facial/api/streaming_status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API statut: {data.get('success')}")
            if data.get('success'):
                status = data.get('status', {})
                print(f"   Streaming: {status.get('is_streaming')}")
                print(f"   Détection: {status.get('detection_enabled')}")
                print(f"   Visages connus: {status.get('known_faces_count')}")
        else:
            print(f"❌ API statut échouée: {response.status_code}")
        
        # 4. Démarrer le streaming
        print("🎬 Démarrage streaming...")
        response = session.post("http://localhost:5002/facial/api/start_streaming")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Streaming démarré")
                
                # Attendre un peu
                time.sleep(3)
                
                # 5. Test du flux vidéo
                print("📺 Test flux vidéo...")
                response = session.get("http://localhost:5002/facial/video_feed", 
                                     stream=True, timeout=10)
                
                if response.status_code == 200:
                    print("✅ Flux vidéo accessible")
                    
                    # Lire quelques chunks
                    chunk_count = 0
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            chunk_count += 1
                            if chunk_count == 1:
                                print(f"✅ Premier chunk reçu: {len(chunk)} bytes")
                                if b'--frame' in chunk:
                                    print("✅ Format multipart détecté")
                                elif b'JFIF' in chunk or b'\xff\xd8' in chunk:
                                    print("✅ Format JPEG détecté")
                                else:
                                    print(f"⚠️ Format inattendu: {chunk[:50]}")
                            
                            if chunk_count >= 3:  # Lire 3 chunks puis arrêter
                                break
                    
                    print(f"✅ {chunk_count} chunks reçus")
                else:
                    print(f"❌ Flux vidéo inaccessible: {response.status_code}")
                
                # 6. Arrêter le streaming
                print("🛑 Arrêt streaming...")
                response = session.post("http://localhost:5002/facial/api/stop_streaming")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print("✅ Streaming arrêté")
                    else:
                        print(f"⚠️ Problème arrêt: {data.get('message')}")
                else:
                    print(f"❌ Erreur arrêt: {response.status_code}")
                
            else:
                print(f"❌ Échec démarrage: {data.get('message')}")
        else:
            print(f"❌ API start_streaming échouée: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_web_streaming()
    
    if success:
        print("\n🎉 Test terminé avec succès!")
        print("💡 Si le streaming fonctionne ici mais pas dans le navigateur,")
        print("   le problème vient probablement du JavaScript ou du cache.")
    else:
        print("\n❌ Test échoué - Vérifiez les erreurs ci-dessus")
