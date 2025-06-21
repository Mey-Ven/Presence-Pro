"""
Script de test pour vérifier le nouveau système de gestion des caméras
Ce script teste la détection et la sélection automatique de la caméra intégrée
"""

import cv2
import time
from camera_manager import CameraManager

def test_camera_detection():
    """Test de détection des caméras"""
    print("🧪 TEST DE DÉTECTION DES CAMÉRAS")
    print("=" * 60)
    
    manager = CameraManager()
    
    # Test 1: Détection des caméras
    print("\n1️⃣ Test de détection des caméras...")
    cameras = manager.detect_cameras()
    
    if not cameras:
        print("❌ ÉCHEC: Aucune caméra détectée")
        return False
    
    print(f"✅ SUCCÈS: {len(cameras)} caméra(s) détectée(s)")
    
    # Test 2: Vérification de la priorité
    print("\n2️⃣ Test de priorité des caméras...")
    builtin_cameras = [cam for cam in cameras if cam['is_builtin']]
    
    if builtin_cameras:
        print(f"✅ SUCCÈS: {len(builtin_cameras)} caméra(s) intégrée(s) détectée(s)")
        for cam in builtin_cameras:
            print(f"   🖥️  {cam['name']} (Index: {cam['index']}, Priorité: {cam['priority']})")
    else:
        print("⚠️  ATTENTION: Aucune caméra intégrée détectée")
    
    # Test 3: Sélection de la meilleure caméra
    print("\n3️⃣ Test de sélection de la meilleure caméra...")
    best_camera = cameras[0]  # La première est la meilleure (triée par priorité)
    
    print(f"🎯 Caméra sélectionnée: {best_camera['name']}")
    print(f"   Index: {best_camera['index']}")
    print(f"   Type: {'🖥️  Intégrée' if best_camera['is_builtin'] else '🔌 Externe'}")
    print(f"   Priorité: {best_camera['priority']}")
    
    return True

def test_camera_initialization():
    """Test d'initialisation de la caméra"""
    print("\n🧪 TEST D'INITIALISATION DE LA CAMÉRA")
    print("=" * 60)
    
    manager = CameraManager()
    
    # Test 1: Obtenir la meilleure caméra
    print("\n1️⃣ Test d'obtention de la meilleure caméra...")
    cap = manager.get_best_camera()
    
    if cap is None:
        print("❌ ÉCHEC: Impossible d'obtenir une caméra")
        return False
    
    print("✅ SUCCÈS: Caméra obtenue")
    
    # Test 2: Vérification du fonctionnement
    print("\n2️⃣ Test de fonctionnement de la caméra...")
    
    try:
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            print("✅ SUCCÈS: Capture d'image réussie")
            print(f"   Taille de l'image: {frame.shape}")
            
            # Test 3: Capture de plusieurs images
            print("\n3️⃣ Test de capture continue...")
            success_count = 0
            total_tests = 5
            
            for i in range(total_tests):
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    success_count += 1
                time.sleep(0.1)
            
            success_rate = (success_count / total_tests) * 100
            print(f"   Taux de réussite: {success_rate:.1f}% ({success_count}/{total_tests})")
            
            if success_rate >= 80:
                print("✅ SUCCÈS: Caméra stable et fonctionnelle")
            else:
                print("⚠️  ATTENTION: Caméra instable")
                
        else:
            print("❌ ÉCHEC: Impossible de capturer une image")
            return False
            
    except Exception as e:
        print(f"❌ ÉCHEC: Erreur lors du test de la caméra: {e}")
        return False
    
    finally:
        cap.release()
    
    return True

def test_camera_preferences():
    """Test des préférences de caméra"""
    print("\n🧪 TEST DES PRÉFÉRENCES DE CAMÉRA")
    print("=" * 60)
    
    manager = CameraManager()
    cameras = manager.detect_cameras()
    
    if not cameras:
        print("❌ ÉCHEC: Aucune caméra pour tester les préférences")
        return False
    
    # Test 1: Vérifier que les caméras intégrées ont une priorité plus élevée
    print("\n1️⃣ Test de priorité des caméras intégrées...")
    
    builtin_cameras = [cam for cam in cameras if cam['is_builtin']]
    external_cameras = [cam for cam in cameras if not cam['is_builtin']]
    
    if builtin_cameras and external_cameras:
        max_builtin_priority = max(cam['priority'] for cam in builtin_cameras)
        max_external_priority = max(cam['priority'] for cam in external_cameras)
        
        if max_builtin_priority > max_external_priority:
            print("✅ SUCCÈS: Les caméras intégrées ont une priorité plus élevée")
        else:
            print("⚠️  ATTENTION: Les caméras externes ont une priorité plus élevée")
    
    # Test 2: Vérifier que l'index 0 est privilégié
    print("\n2️⃣ Test de privilège de l'index 0...")
    
    camera_0 = next((cam for cam in cameras if cam['index'] == 0), None)
    if camera_0:
        if camera_0['is_builtin']:
            print("✅ SUCCÈS: La caméra index 0 est marquée comme intégrée")
        else:
            print("⚠️  ATTENTION: La caméra index 0 n'est pas marquée comme intégrée")
    else:
        print("⚠️  ATTENTION: Aucune caméra à l'index 0")
    
    return True

def test_live_preview():
    """Test avec aperçu en direct"""
    print("\n🧪 TEST AVEC APERÇU EN DIRECT")
    print("=" * 60)
    
    manager = CameraManager()
    cap = manager.get_best_camera()
    
    if cap is None:
        print("❌ ÉCHEC: Impossible d'obtenir une caméra pour l'aperçu")
        return False
    
    camera_info = manager.get_camera_info()
    
    print("\n📹 Démarrage de l'aperçu en direct...")
    print("   Appuyez sur 'q' pour quitter")
    print("   Appuyez sur 's' pour prendre une capture d'écran")
    
    try:
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Erreur lors de la lecture de la caméra")
                break
            
            frame_count += 1
            
            # Ajouter des informations sur l'image
            cv2.putText(frame, f"Camera: {camera_info['name']}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(frame, f"Index: {camera_info['index']}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            camera_type = "Built-in" if camera_info['is_builtin'] else "External"
            cv2.putText(frame, f"Type: {camera_type}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Calculer et afficher les FPS
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                fps = frame_count / elapsed_time
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(frame, "Press 'q' to quit, 's' for screenshot", (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow("Camera Test - Live Preview", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                screenshot_name = f"camera_test_screenshot_{int(time.time())}.jpg"
                cv2.imwrite(screenshot_name, frame)
                print(f"📸 Capture d'écran sauvegardée: {screenshot_name}")
        
        print(f"✅ SUCCÈS: Aperçu terminé ({frame_count} images traitées)")
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC: Erreur lors de l'aperçu: {e}")
        return False
    
    finally:
        cap.release()
        cv2.destroyAllWindows()

def main():
    """Fonction principale de test"""
    print("🎥 SYSTÈME DE TEST DES CAMÉRAS")
    print("=" * 60)
    print("Ce script teste le nouveau système de gestion des caméras")
    print("qui privilégie automatiquement la caméra intégrée de l'ordinateur.")
    print()
    
    # Exécuter tous les tests
    tests = [
        ("Détection des caméras", test_camera_detection),
        ("Initialisation de la caméra", test_camera_initialization),
        ("Préférences de caméra", test_camera_preferences),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 EXÉCUTION: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
            print(f"   Résultat: {status}")
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            results.append((test_name, False))
    
    # Résumé des résultats
    print("\n📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 RÉSULTAT GLOBAL: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("   Le système de caméra fonctionne correctement.")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("   Vérifiez la configuration de vos caméras.")
    
    # Proposer le test d'aperçu en direct
    if passed > 0:
        print("\n🎬 Test d'aperçu en direct disponible")
        response = input("Voulez-vous tester l'aperçu en direct? (o/n): ").lower().strip()
        if response in ['o', 'oui', 'y', 'yes']:
            test_live_preview()

if __name__ == "__main__":
    main()
