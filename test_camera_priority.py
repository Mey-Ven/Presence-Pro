"""
Test pour vérifier la priorité des caméras et s'assurer que la caméra intégrée (index 0) est sélectionnée
"""

from camera_manager import CameraManager
import cv2

def test_camera_priority():
    """Test de la priorité des caméras"""
    print("🎥 TEST DE PRIORITÉ DES CAMÉRAS")
    print("=" * 60)
    print("Ce test vérifie que la caméra intégrée (index 0) est prioritaire")
    print()
    
    # Créer le gestionnaire de caméras
    manager = CameraManager()
    
    # Détecter toutes les caméras
    print("🔍 Détection de toutes les caméras...")
    cameras = manager.detect_cameras()
    
    if not cameras:
        print("❌ Aucune caméra détectée")
        return False
    
    print(f"\n📷 {len(cameras)} caméra(s) détectée(s):")
    for i, cam in enumerate(cameras):
        builtin_status = "🖥️  INTÉGRÉE" if cam['is_builtin'] else "🔌 EXTERNE"
        print(f"   {i+1}. Index {cam['index']}: {cam['name']}")
        print(f"      Type: {builtin_status}")
        print(f"      Priorité: {cam['priority']}")
        print()
    
    # Vérifier que l'index 0 est présent et prioritaire
    index_0_found = False
    index_0_priority = 0
    
    for cam in cameras:
        if cam['index'] == 0:
            index_0_found = True
            index_0_priority = cam['priority']
            print(f"✅ Caméra index 0 trouvée:")
            print(f"   Nom: {cam['name']}")
            print(f"   Type: {'🖥️  INTÉGRÉE' if cam['is_builtin'] else '🔌 EXTERNE'}")
            print(f"   Priorité: {cam['priority']}")
            break
    
    if not index_0_found:
        print("⚠️ ATTENTION: Caméra index 0 non trouvée!")
        print("   Cela peut indiquer que votre caméra intégrée n'est pas accessible")
        print("   ou qu'elle est utilisée par une autre application.")
        return False
    
    # Vérifier que l'index 0 a la priorité la plus élevée
    highest_priority = max(cam['priority'] for cam in cameras)
    
    if index_0_priority == highest_priority:
        print("✅ PARFAIT: La caméra index 0 a la priorité la plus élevée!")
    else:
        print("⚠️ PROBLÈME: La caméra index 0 n'a pas la priorité la plus élevée")
        print(f"   Priorité index 0: {index_0_priority}")
        print(f"   Priorité maximale: {highest_priority}")
    
    # Tester la sélection de la meilleure caméra
    print("\n🎯 Test de sélection de la meilleure caméra...")
    best_camera = manager.get_best_camera()
    
    if best_camera:
        selected_info = manager.get_camera_info()
        if selected_info:
            print(f"✅ Caméra sélectionnée: Index {selected_info['index']}")
            print(f"   Nom: {selected_info['name']}")
            print(f"   Type: {'🖥️  INTÉGRÉE' if selected_info['is_builtin'] else '🔌 EXTERNE'}")
            
            if selected_info['index'] == 0:
                print("🎉 EXCELLENT: La caméra index 0 (intégrée) a été sélectionnée!")
                success = True
            else:
                print(f"⚠️ PROBLÈME: La caméra index {selected_info['index']} a été sélectionnée au lieu de 0")
                success = False
        else:
            print("❌ Impossible d'obtenir les informations de la caméra sélectionnée")
            success = False
        
        # Libérer la caméra
        best_camera.release()
    else:
        print("❌ Aucune caméra n'a pu être sélectionnée")
        success = False
    
    return success

def test_manual_camera_0():
    """Test manuel de la caméra index 0"""
    print("\n🔧 TEST MANUEL DE LA CAMÉRA INDEX 0")
    print("=" * 60)
    
    try:
        # Tester directement l'index 0
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            print("✅ Caméra index 0 accessible directement")
            
            # Tester la capture
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                print(f"✅ Capture réussie: {frame.shape}")
                print("✅ La caméra index 0 fonctionne parfaitement")
                success = True
            else:
                print("❌ Échec de la capture d'image")
                success = False
            
            cap.release()
        else:
            print("❌ Impossible d'ouvrir la caméra index 0")
            success = False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        success = False
    
    return success

def main():
    """Fonction principale"""
    print("🎯 TESTEUR DE PRIORITÉ DES CAMÉRAS")
    print("Ce script vérifie que votre caméra intégrée (index 0) est correctement détectée et prioritaire")
    print()
    
    # Test 1: Priorité des caméras
    priority_success = test_camera_priority()
    
    # Test 2: Test manuel de l'index 0
    manual_success = test_manual_camera_0()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    print(f"Test de priorité: {'✅ RÉUSSI' if priority_success else '❌ ÉCHOUÉ'}")
    print(f"Test manuel index 0: {'✅ RÉUSSI' if manual_success else '❌ ÉCHOUÉ'}")
    
    if priority_success and manual_success:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("   ✅ Votre caméra intégrée sera correctement sélectionnée")
        print("   ✅ Le système utilisera l'index 0 par défaut")
        print("   ✅ Priorité correctement configurée")
    elif manual_success:
        print("\n⚠️ TESTS PARTIELLEMENT RÉUSSIS")
        print("   ✅ La caméra index 0 fonctionne")
        print("   ⚠️ Mais la priorité peut nécessiter des ajustements")
    else:
        print("\n❌ PROBLÈMES DÉTECTÉS")
        print("   ❌ La caméra index 0 n'est pas accessible")
        print("   💡 Vérifiez qu'aucune autre application n'utilise la caméra")
        print("   💡 Redémarrez l'ordinateur si nécessaire")
    
    print("\n💡 RECOMMANDATIONS:")
    if priority_success and manual_success:
        print("   🎯 Le système est correctement configuré")
        print("   🎯 La reconnaissance faciale utilisera votre caméra intégrée")
    else:
        print("   🔧 Fermez toutes les applications utilisant la caméra")
        print("   🔧 Redémarrez l'ordinateur")
        print("   🔧 Vérifiez les permissions de caméra dans les paramètres système")

if __name__ == "__main__":
    main()
