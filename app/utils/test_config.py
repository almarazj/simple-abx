"""
Configuración y utilidades específicas para el test ABX
"""
import random
import json
from pathlib import Path

def get_audio_pairs_list():
    """
    Lee el archivo metadata.json y devuelve una lista de diccionarios con los pares de audio
    para el test ABX (drum, vocal, flute, etc).
    """
    metadata_path = Path('static/audio/test_files/metadata.json')
    if not metadata_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo {metadata_path}")

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    pairs = []
    for stimulus in metadata.get('stimuli', []):
        stimulus_type = stimulus.get('id')
        reference_file = stimulus.get('reference_file')
        for variation in stimulus.get('variations', []):
            pairs.append({
                'id': f"{stimulus_type}_{variation.get('pulse_density')}",
                'stimulus_type': stimulus_type,
                'pulse_density': variation.get('pulse_density'),
                'reference': reference_file,
                'variation': variation.get('file')
            })
    return pairs

    
def generate_test_sequence():
    """Generar secuencia aleatoria de 21 comparaciones ABX (7 variaciones × 3 estímulos)"""
    # Obtener pares de audio disponibles
    audio_pairs = get_audio_pairs_list()
    
    if not audio_pairs:
        raise ValueError("No hay archivos de audio disponibles para el test")
    
    # Randomizar el orden de presentación
    random.shuffle(audio_pairs)
    
    comparisons = []
    
    for i, pair in enumerate(audio_pairs):
        # En este test: Reference = GWN (stimulus A), Variation = Velvet Noise (stimulus B)
        reference_file = pair['reference']  # GWN file
        variation_file = pair['variation']   # Velvet noise file
        
        # Decidir aleatoriamente cuál es A y cuál es B
        if random.choice([True, False]):
            stimulus_a = reference_file
            stimulus_b = variation_file
            a_type = 'reference'
            b_type = 'variation'
        else:
            stimulus_a = variation_file
            stimulus_b = reference_file
            a_type = 'variation'
            b_type = 'reference'
        
        # X es siempre uno de los dos (aleatorio)
        if random.choice([True, False]):
            stimulus_x = stimulus_a
            correct_answer = 'a'
            x_type = a_type
        else:
            stimulus_x = stimulus_b
            correct_answer = 'b'
            x_type = b_type
        
        comparison = {
            'id': i,
            'stimulus_a': stimulus_a,
            'stimulus_b': stimulus_b,
            'stimulus_x': stimulus_x,
            'correct_answer': correct_answer,
            'pair_info': {
                'pair_id': pair['id'],
                'stimulus_type': pair['stimulus_type'],
                'pulse_density': pair['pulse_density'],
                'reference_file': pair['reference'],
                'variation_file': pair['variation'],
                'a_type': a_type,  # 'reference' or 'variation'
                'b_type': b_type,  # 'reference' or 'variation'
                'x_type': x_type   # 'reference' or 'variation'
            }
        }
        comparisons.append(comparison)
    return comparisons
