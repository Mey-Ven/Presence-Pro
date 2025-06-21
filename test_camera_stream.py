"""
Test pour diagnostiquer les problèmes de flux caméra
"""

import cv2
import base64
import time
from camera_manager import CameraManager

def test_camera_stream():
    """Test du flux caméra pour diagnostiquer les problèmes"""
    print("🎥 TEST DU FLUX CAMÉRA")
    print("=" * 60)
    
    # Test 1: Gestionnaire de caméras
    print("1️⃣ Test du gestionnaire de caméras...")
    manager = CameraManager()
    cameras = manager.detect_cameras()
    
    if not cameras:
        print("❌ Aucune caméra détectée")
        return False
    
    print(f"✅ {len(cameras)} caméra(s) détectée(s)")
    for cam in cameras:
        print(f"   - Index {cam['index']}: {cam['name']} ({'Intégrée' if cam['is_builtin'] else 'Externe'})")
    
    # Test 2: Sélection de la meilleure caméra
    print("\n2️⃣ Test de sélection de caméra...")
    best_camera = manager.get_best_camera()
    
    if not best_camera:
        print("❌ Impossible de sélectionner une caméra")
        return False
    
    camera_info = manager.get_camera_info()
    print(f"✅ Caméra sélectionnée: Index {camera_info['index']} - {camera_info['name']}")
    
    # Test 3: Capture d'images
    print("\n3️⃣ Test de capture d'images...")
    
    success_count = 0
    total_tests = 10
    
    for i in range(total_tests):
        ret, frame = best_camera.read()
        if ret and frame is not None and frame.size > 0:
            success_count += 1
            print(f"   Frame {i+1}: ✅ {frame.shape}")
        else:
            print(f"   Frame {i+1}: ❌ Échec")
        time.sleep(0.1)
    
    success_rate = (success_count / total_tests) * 100
    print(f"\n📊 Taux de réussite: {success_rate:.1f}% ({success_count}/{total_tests})")
    
    # Test 4: Encodage base64
    print("\n4️⃣ Test d'encodage base64...")
    
    ret, frame = best_camera.read()
    if ret and frame is not None:
        try:
            # Redimensionner comme dans le contrôleur
            display_frame = cv2.resize(frame, (640, 480))
            
            # Encoder en JPEG
            _, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            
            # Encoder en base64
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            print(f"✅ Encodage réussi: {len(frame_base64)} caractères")
            print(f"   Taille originale: {frame.shape}")
            print(f"   Taille redimensionnée: {display_frame.shape}")
            print(f"   Taille buffer JPEG: {len(buffer)} bytes")
            
        except Exception as e:
            print(f"❌ Erreur d'encodage: {e}")
            best_camera.release()
            return False
    else:
        print("❌ Impossible de capturer une frame pour l'encodage")
        best_camera.release()
        return False
    
    # Test 5: Test de performance
    print("\n5️⃣ Test de performance...")
    
    start_time = time.time()
    frames_processed = 0
    
    for i in range(50):  # Test sur 50 frames
        ret, frame = best_camera.read()
        if ret and frame is not None:
            # Simuler le traitement du contrôleur
            display_frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            frames_processed += 1
        time.sleep(0.033)  # ~30 FPS
    
    end_time = time.time()
    duration = end_time - start_time
    fps = frames_processed / duration
    
    print(f"✅ Performance: {fps:.1f} FPS ({frames_processed} frames en {duration:.1f}s)")
    
    # Libérer la caméra
    best_camera.release()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DU TEST")
    print("=" * 60)
    
    all_good = success_rate >= 90 and fps >= 15
    
    if all_good:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("   ✅ Caméra détectée et fonctionnelle")
        print("   ✅ Capture d'images stable")
        print("   ✅ Encodage base64 fonctionnel")
        print("   ✅ Performance acceptable")
        print("\n💡 Le problème de flux noir peut venir de:")
        print("   - WebSocket non connecté")
        print("   - JavaScript côté client")
        print("   - Permissions de caméra")
    else:
        print("⚠️ PROBLÈMES DÉTECTÉS!")
        if success_rate < 90:
            print(f"   ❌ Taux de capture faible: {success_rate:.1f}%")
        if fps < 15:
            print(f"   ❌ Performance insuffisante: {fps:.1f} FPS")
        print("\n💡 Actions recommandées:")
        print("   - Fermer autres applications utilisant la caméra")
        print("   - Redémarrer l'ordinateur")
        print("   - Vérifier les permissions système")
    
    return all_good

def test_direct_camera():
    """Test direct de la caméra sans gestionnaire"""
    print("\n🔧 TEST DIRECT DE LA CAMÉRA")
    print("=" * 60)
    
    # Tester directement l'index 0
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la caméra index 0")
        return False
    
    print("✅ Caméra index 0 ouverte")
    
    # Configurer la caméra
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Obtenir les propriétés réelles
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"📐 Résolution: {width}x{height}")
    print(f"🎬 FPS: {fps}")
    
    # Test de capture
    success_count = 0
    for i in range(10):
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            success_count += 1
            print(f"   Frame {i+1}: ✅ {frame.shape}")
        else:
            print(f"   Frame {i+1}: ❌ Échec")
        time.sleep(0.1)
    
    cap.release()
    
    success_rate = (success_count / 10) * 100
    print(f"\n📊 Taux de réussite direct: {success_rate:.1f}%")
    
    return success_rate >= 90

def main():
    """Fonction principale"""
    print("🎯 DIAGNOSTIC DU FLUX CAMÉRA")
    print("Ce test diagnostique les problèmes de flux caméra noir")
    print()
    
    # Test avec gestionnaire
    manager_success = test_camera_stream()
    
    # Test direct
    direct_success = test_direct_camera()
    
    # Conclusion
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC FINAL")
    print("=" * 60)
    
    if manager_success and direct_success:
        print("✅ CAMÉRA PARFAITEMENT FONCTIONNELLE")
        print("   Le problème de flux noir vient probablement de:")
        print("   1. WebSocket non connecté au dashboard")
        print("   2. JavaScript côté client")
        print("   3. Contrôleur de reconnaissance non démarré")
        print("\n💡 Solutions:")
        print("   - Vérifier la console JavaScript du navigateur")
        print("   - Redémarrer le dashboard")
        print("   - Vérifier que la reconnaissance est bien démarrée")
    elif direct_success:
        print("⚠️ PROBLÈME AVEC LE GESTIONNAIRE DE CAMÉRAS")
        print("   La caméra fonctionne mais le gestionnaire a des problèmes")
        print("\n💡 Solutions:")
        print("   - Vérifier le code du CameraManager")
        print("   - Utiliser directement cv2.VideoCapture(0)")
    else:
        print("❌ PROBLÈME MATÉRIEL OU SYSTÈME")
        print("   La caméra ne fonctionne pas correctement")
        print("\n💡 Solutions:")
        print("   - Fermer toutes les applications utilisant la caméra")
        print("   - Redémarrer l'ordinateur")
        print("   - Vérifier les permissions de caméra")
        print("   - Tester avec une autre application (Photo, FaceTime)")

if __name__ == "__main__":
    main()
