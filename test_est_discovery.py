import sys
import os

# Add script directory to path
script_dir = os.path.abspath(os.path.join(os.getcwd(), 'script'))
sys.path.append(script_dir)

from document_processor import discover_files, CONFIG

def test_est_discovery():
    print("Testing ESt Discovery Logic...")
    
    # Mock files that mimic ESt documents
    mock_files = [
        "Daten Franklin\\BaM Übersendung JA digital 2024.docx",
        "Daten Franklin\\Deckblatt Einkommensteuer 2024.docx",
        "Daten Franklin\\ESt Erklärung 2024.pdf",
        "Daten Franklin\\ESt Erklärung Freizeichnungsdokument 2024.pdf",
    ]
    
    # We need to monkeypatch glob.glob for discover_files to work without real files
    import glob
    original_glob = glob.glob
    glob.glob = lambda x: mock_files if "*" in x else []
    
    # Mock os.path.exists
    original_exists = os.path.exists
    os.path.exists = lambda x: True
    
    # Mock os.path.basename
    original_basename = os.path.basename
    os.path.basename = lambda x: x.split("\\")[-1]
    
    try:
        found = discover_files("mock_dir")
        
        print("\nResults:")
        for dt, paths in found.items():
            print(f"Type: {dt}")
            for p in paths:
                print(f"  - {p}")
                
        # Assertions
        assert 'est' in found, "ESt not found"
        assert 'est_freizeichnung' in found, "ESt Freizeichnung not found"
        assert 'deckblatt_steuererklaerung' in found, "Deckblatt not found"
        
        # Verify Deckblatt caught the right file
        deckblatt_files = [os.path.basename(p) for p in found['deckblatt_steuererklaerung']]
        assert "Deckblatt Einkommensteuer 2024.docx" in deckblatt_files, "Deckblatt ESt not matched"
        
        print("\nDiscovery Logic Verification: PASSED")
        
    finally:
        # Restore original functions
        glob.glob = original_glob
        os.path.exists = original_exists
        os.path.basename = original_basename

if __name__ == "__main__":
    test_est_discovery()
