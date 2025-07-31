import random
from pathlib import Path
from app.schemas.metadata import TestMetadata, AudioPair
from app.schemas.test_results import Comparison, PairInfo

def get_audio_pairs_list():
    """
    Lee el archivo metadata.json y devuelve una lista de diccionarios con los pares de audio
    para el test ABX (drum, vocal, flute, etc).
    """
    metadata_path = Path('static/audio/test_files/metadata.json')
    if not metadata_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo {metadata_path}")

    with open('static/audio/test_files/metadata.json', 'r', encoding='utf-8') as f:
        metadata = TestMetadata.model_validate_json(f.read())

    stimuli = metadata.stimuli.copy()
    
    # Randomly drop one of the stimuli to have 14 variants
    stimuli.remove(random.choice(stimuli))

    pairs = []
    for stimulus in stimuli:
        stimulus_type = stimulus.id
        reference_file = stimulus.reference_file
        for variation in stimulus.variations:
            pair = AudioPair(
                id=f"{stimulus_type}_{variation.pulse_density}",
                stimulus_type=stimulus_type,
                pulse_density=variation.pulse_density,
                reference=reference_file,
                variation=variation.file
            )
            pairs.append(pair)
    return pairs

    
def generate_test_sequence():
    """Generar secuencia aleatoria de 21 comparaciones ABX (7 variaciones × 3 estímulos)"""
    # Obtener pares de audio disponibles
    audio_pairs = get_audio_pairs_list()
    if not audio_pairs:
        raise ValueError("No hay archivos de audio disponibles para el test")
    
    random.shuffle(audio_pairs)
    
    comparisons = []
    
    for i, pair in enumerate(audio_pairs):
        reference_file = pair.reference
        variation_file = pair.variation
        
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
            
        pair_info = PairInfo(
            a_type=a_type,
            b_type=b_type,
            pair_id=pair.id,
            pulse_density=pair.pulse_density,
            reference_file=reference_file,
            stimulus_type=pair.stimulus_type,
            variation_file=variation_file,
            x_type=x_type,
        )
        comparison = Comparison(
            id=i,
            correct_answer=correct_answer,
            pair_info=pair_info,
            stimulus_a=stimulus_a,
            stimulus_b=stimulus_b,
            stimulus_x=stimulus_x
        )
        comparisons.append(comparison)
    return comparisons
