import Levenshtein

def levenshtein_similarity(str1, str2):
    # Calculate the Levenshtein distance
    distance = Levenshtein.distance(str1, str2)
    
    # Determine the maximum possible length
    max_len = max(len(str1), len(str2))
    
    if max_len == 0:
        return 100.0  # If both strings are empty, they are identical
    
    # Calculate the similarity as a percentage
    similarity_percentage = (1 - (distance / max_len)) * 100
    
    return similarity_percentage
