#!/usr/bin/env python3
"""
Test rapide du streaming dans la gestion
"""

import requests

def quick_test():
    session = requests.Session()
    
    # Connexion
    login_data = {'username': 'admin', 'password': 'admin123'}
    session.post("http://localhost:5002/login", data=login_data)
    
    # Test page gestion
    response = session.get("http://localhost:5002/facial/manage_detections")
    
    if response.status_code == 200:
        content = response.text
        
        checks = [
            "Streaming Vidéo en Temps Réel",
            "managementVideoFeed",
            "Démarrer Caméra",
            "startCamera()",
            "video-section"
        ]
        
        print("🎥 TEST RAPIDE STREAMING GESTION:")
        for check in checks:
            if check in content:
                print(f"✅ {check}: Présent")
            else:
                print(f"❌ {check}: Manquant")
        
        # Test API streaming
        response = session.post("http://localhost:5002/facial/api/start_streaming")
        if response.status_code == 200:
            data = response.json()
            print(f"🎬 API Streaming: {'✅ OK' if data.get('success') else '❌ Erreur'}")
            
            # Arrêter
            session.post("http://localhost:5002/facial/api/stop_streaming")
        else:
            print(f"❌ API Streaming: Erreur {response.status_code}")
    else:
        print(f"❌ Page inaccessible: {response.status_code}")

if __name__ == "__main__":
    quick_test()
