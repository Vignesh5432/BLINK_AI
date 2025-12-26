import mediapipe as mp
print("Mediapie imported:", mp)
try:
    print("mp.solutions:", mp.solutions)
except AttributeError as e:
    print("mp.solutions error:", e)
    print("Dir mp:", dir(mp))
    
    try:
        import mediapipe.python.solutions
        print("Explicit import worked")
    except ImportError as ie:
        print("Explicit import failed:", ie)
