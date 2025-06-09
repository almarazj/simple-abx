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
        stimulus_name = stimulus.get('name')
        reference_file = stimulus.get('reference_file')
        for variation in stimulus.get('variations', []):
            pairs.append({
                'id': f"{stimulus_type}_{variation.get('id')}",
                'stimulus_type': stimulus_type,
                'stimulus_name': stimulus_name,
                'variation_id': variation.get('id'),
                'variation_description': variation.get('description'),
                'reference': reference_file,
                'variation': variation.get('file')
            })
    return pairs

class ABXTestGenerator:
    """Generador de secuencias de test ABX para GWN vs Velvet Noise"""
    
    def __init__(self, num_comparisons=21):
        self.num_comparisons = num_comparisons
    
    def generate_test_sequence(self):
        """Generar secuencia aleatoria de 21 comparaciones ABX (7 variaciones × 3 estímulos)"""
        # Obtener pares de audio disponibles
        audio_pairs = get_audio_pairs_list()
        
        if not audio_pairs:
            raise ValueError("No hay archivos de audio disponibles para el test")
        
        # Verificar que tenemos exactamente 21 pares (7 por cada estímulo)
        drum_pairs = [p for p in audio_pairs if p['stimulus_type'] == 'drum']
        vocal_pairs = [p for p in audio_pairs if p['stimulus_type'] == 'vocal']
        flute_pairs = [p for p in audio_pairs if p['stimulus_type'] == 'flute']
        
        if len(drum_pairs) != 7 or len(vocal_pairs) != 7 or len(flute_pairs) != 7:
            print(f"Advertencia: Se esperaban 7 variaciones por estímulo. Encontrados: Drum={len(drum_pairs)}, Vocal={len(vocal_pairs)}, Flute={len(flute_pairs)}")
        
        # Combinar todos los pares disponibles
        all_pairs = drum_pairs + vocal_pairs + flute_pairs
        
        # Tomar solo los primeros 21 si hay más, o usar todos si hay menos
        pairs_to_use = all_pairs[:21] if len(all_pairs) >= 21 else all_pairs
        
        # Randomizar el orden de presentación
        random.shuffle(pairs_to_use)
        
        comparisons = []
        
        for i, pair in enumerate(pairs_to_use):
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
                correct_answer = 'A'
                x_type = a_type
            else:
                stimulus_x = stimulus_b
                correct_answer = 'B'
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
                    'stimulus_name': pair['stimulus_name'],
                    'variation_id': pair['variation_id'],
                    'variation_description': pair['variation_description'],
                    'reference_file': pair['reference'],
                    'variation_file': pair['variation'],
                    'a_type': a_type,  # 'reference' or 'variation'
                    'b_type': b_type,  # 'reference' or 'variation'
                    'x_type': x_type   # 'reference' or 'variation'
                }
            }
            
            comparisons.append(comparison)
        
        return comparisons
    
    def validate_test_sequence(self, comparisons):
        """Validar que la secuencia de test es válida"""
        if not comparisons:
            return False, "No hay comparaciones en la secuencia"
        
        if len(comparisons) < 1:
            return False, "Secuencia muy corta"
        
        # Verificar que cada comparación tiene los campos necesarios
        required_fields = ['id', 'stimulus_a', 'stimulus_b', 'stimulus_x', 'correct_answer']
        
        for i, comp in enumerate(comparisons):
            for field in required_fields:
                if field not in comp:
                    return False, f"Comparación {i} falta campo '{field}'"
            
            if comp['correct_answer'] not in ['A', 'B']:
                return False, f"Comparación {i} tiene respuesta correcta inválida: {comp['correct_answer']}"
        
        return True, None

class TestStatistics:
    """Calculador de estadísticas del test"""
    
    @staticmethod
    def calculate_basic_stats(responses):
        """Calcular estadísticas básicas del test"""
        if not responses:
            return {
                'total_comparisons': 0,
                'correct_responses': 0,
                'incorrect_responses': 0,
                'tie_responses': 0,
                'accuracy_percentage': 0
            }
        
        total_responses = len(responses)
        correct_responses = sum(1 for r in responses if r.get('is_correct', False))
        tie_responses = sum(1 for r in responses if r.get('user_response') == 'tie')
        incorrect_responses = total_responses - correct_responses - tie_responses
        
        # Calcular precisión excluyendo empates
        non_tie_responses = total_responses - tie_responses
        accuracy = (correct_responses / non_tie_responses * 100) if non_tie_responses > 0 else 0
        
        return {
            'total_comparisons': total_responses,
            'correct_responses': correct_responses,
            'incorrect_responses': incorrect_responses,
            'tie_responses': tie_responses,
            'accuracy_percentage': round(accuracy, 1)
        }
    
    @staticmethod
    def calculate_detailed_stats(responses):
        """Calcular estadísticas detalladas"""
        basic_stats = TestStatistics.calculate_basic_stats(responses)
        
        if not responses:
            return basic_stats
        
        detailed_stats = basic_stats.copy()
        detailed_stats.update({
            'response_pattern': TestStatistics._analyze_response_pattern(responses),
            'confidence_estimate': TestStatistics._estimate_confidence(responses),
            'velvet_noise_analysis': TestStatistics._analyze_velvet_noise_performance(responses)
        })
        
        return detailed_stats
    
    @staticmethod
    def _calculate_std_dev(values):
        """Calcular desviación estándar"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    @staticmethod
    def _analyze_response_pattern(responses):
        """Analizar patrones en las respuestas"""
        if not responses:
            return {}
        
        response_counts = {'A': 0, 'B': 0, 'tie': 0}
        correct_by_position = {}
        
        for i, response in enumerate(responses):
            user_resp = response.get('user_response', 'tie')
            response_counts[user_resp] = response_counts.get(user_resp, 0) + 1
            
            # Analizar precisión por posición en el test
            position_group = i // 5  # Grupos de 5
            if position_group not in correct_by_position:
                correct_by_position[position_group] = {'correct': 0, 'total': 0}
            
            correct_by_position[position_group]['total'] += 1
            if response.get('is_correct', False):
                correct_by_position[position_group]['correct'] += 1
        
        return {
            'response_distribution': response_counts,
            'accuracy_by_position': correct_by_position
        }
    
    @staticmethod
    def _estimate_confidence(responses):
        """Estimar nivel de confianza del participante"""
        if not responses:
            return 0
        
        # Usar empates como proxy de confianza
        # Menos empates = más confianza
        tie_ratio = sum(1 for r in responses if r.get('user_response') == 'tie') / len(responses)
        
        # Escala simple: menos empates = más confianza
        confidence = (1 - tie_ratio) * 100
        
        return round(min(100, max(0, confidence)), 1)
    
    @staticmethod
    def _analyze_velvet_noise_performance(responses):
        """Analizar rendimiento específico para el test GWN vs Velvet Noise"""
        if not responses:
            return {}
        
        # Analizar por tipo de estímulo
        stimulus_performance = {}
        variation_performance = {}
        
        for response in responses:
            pair_info = response.get('pair_info', {})
            stimulus_type = pair_info.get('stimulus_type', 'unknown')
            variation_id = pair_info.get('variation_id', 'unknown')
            is_correct = response.get('is_correct', False)
            user_response = response.get('user_response', 'tie')
            
            # Estadísticas por tipo de estímulo
            if stimulus_type not in stimulus_performance:
                stimulus_performance[stimulus_type] = {'correct': 0, 'total': 0, 'tie': 0}
            
            stimulus_performance[stimulus_type]['total'] += 1
            if user_response == 'tie':
                stimulus_performance[stimulus_type]['tie'] += 1
            elif is_correct:
                stimulus_performance[stimulus_type]['correct'] += 1
            
            # Estadísticas por variación de velvet noise
            if variation_id not in variation_performance:
                variation_performance[variation_id] = {'correct': 0, 'total': 0, 'tie': 0}
            
            variation_performance[variation_id]['total'] += 1
            if user_response == 'tie':
                variation_performance[variation_id]['tie'] += 1
            elif is_correct:
                variation_performance[variation_id]['correct'] += 1
        
        # Calcular porcentajes
        for stimulus, stats in stimulus_performance.items():
            non_tie = stats['total'] - stats['tie']
            stats['accuracy_percentage'] = (stats['correct'] / non_tie * 100) if non_tie > 0 else 0
            stats['tie_percentage'] = (stats['tie'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        for variation, stats in variation_performance.items():
            non_tie = stats['total'] - stats['tie']
            stats['accuracy_percentage'] = (stats['correct'] / non_tie * 100) if non_tie > 0 else 0
            stats['tie_percentage'] = (stats['tie'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return {
            'stimulus_performance': stimulus_performance,
            'variation_performance': variation_performance,
            'difficulty_ranking': TestStatistics._rank_variations_by_difficulty(variation_performance)
        }
    
    @staticmethod
    def _rank_variations_by_difficulty(variation_performance):
        """Clasificar variaciones por dificultad basado en precisión"""
        if not variation_performance:
            return []
        
        # Crear lista de variaciones con su precisión
        variations_with_accuracy = []
        for variation_id, stats in variation_performance.items():
            accuracy = stats.get('accuracy_percentage', 0)
            tie_percentage = stats.get('tie_percentage', 0)
            
            # Considerar tanto la precisión como el porcentaje de empates para la dificultad
            # Mayor precisión = más fácil, más empates = más difícil
            difficulty_score = accuracy - (tie_percentage * 0.5)  # Penalizar empates
            
            variations_with_accuracy.append({
                'variation_id': variation_id,
                'accuracy_percentage': accuracy,
                'tie_percentage': tie_percentage,
                'difficulty_score': difficulty_score,
                'total_responses': stats.get('total', 0)
            })
        
        # Ordenar por score de dificultad (mayor score = más fácil)
        variations_with_accuracy.sort(key=lambda x: x['difficulty_score'], reverse=True)
        
        return variations_with_accuracy

# Configuraciones predefinidas del test
TEST_CONFIGURATIONS = {
    'velvet_noise_full': {
        'name': 'Test Completo GWN vs Velvet Noise',
        'num_comparisons': 21,
        'description': 'Test completo con 21 comparaciones (7 variaciones × 3 estímulos)'
    },
    'velvet_noise_quick': {
        'name': 'Test Rápido GWN vs Velvet Noise',
        'num_comparisons': 9,
        'description': 'Test rápido con 9 comparaciones (3 variaciones × 3 estímulos)'
    },
    'velvet_noise_single': {
        'name': 'Test Individual por Estímulo',
        'num_comparisons': 7,
        'description': 'Test de un solo estímulo con 7 variaciones'
    },
    'standard': {
        'name': 'Test Estándar (Legacy)',
        'num_comparisons': 10,
        'description': 'Test estándar para compatibilidad'
    }
}

def get_test_config(config_name='velvet_noise_full'):
    """Obtener configuración de test por nombre"""
    return TEST_CONFIGURATIONS.get(config_name, TEST_CONFIGURATIONS['velvet_noise_full'])