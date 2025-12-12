import numpy as np
import pickle
import os
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVR
from core.vectorizer import Vectorizer

class ModelTrainer:
    """
    Antigravity Engine V2.0 - Training Module
    
    1. Loads Vectorized Data (X, Y) using Physics-based Vectorizer.
    2. Trains Lightweight Models (Logistic Regression / SVM).
    3. Handles Cold Start vs. Iterative Updates.
    """
    def __init__(self, model_dir="data/models"):
        self.vectorizer = Vectorizer()
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Models for different aspects
        self.models = {} 
        
    def train(self, aspect="wealth", algorithm="logistic"):
        """
        Main training loop for a specific life aspect.
        """
        print(f"Adding quantum vectors for aspect: {aspect}...")
        
        # 1. Load Data
        # X: [Energy_Wood, Energy_Fire..., Bit_Jia, Bit_Yi...]
        # Y: [75, 80, 40...] (Continuous Scores)
        X, y = self.vectorizer.load_dataset(target_aspect=aspect)
        
        if len(X) == 0:
            print("⚠️ No field data found in DB. Applying Cold Start (Physics Priors)...")
            return self._apply_cold_start(aspect)

        print(f"Training on {len(X)} cases. Vector Dim: {X.shape[1]}")

        # 2. Select Algorithm
        if algorithm == "logistic":
            from sklearn.linear_model import Ridge
            model = Ridge(alpha=1.0)
            print("Using Ridge Regression (Linear Model).")
            
        elif algorithm == "svm":
            model = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=.1)
            print("Using SVM (Regression).")
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
            
        # 3. Fit
        model.fit(X, y)
        self._save_model(model, aspect)
        return True

    def _apply_cold_start(self, aspect):
        """
        Creates a 'Cold Start' model based on blueprint weights (W_career) 
        without needing actual training data.
        """
        # We can't easily inject weights into an unsold SVR. 
        # Strategy: Create Synthetic Data based on Rules!
        # Or: Create a simple Linear Model and set coefficients manually.
        
        print(f"  -> Synthesizing rules for {aspect}...")
        
        # 1. Create a Ridge Model (Linear)
        from sklearn.linear_model import Ridge
        model = Ridge(alpha=1.0)
        
        # 2. Determine coefficients from Vectorizer.W_CAREER
        # Our Vector has 5 Energies (Wood...Water) + 88 Raw.
        # W_CAREER maps 'Ten Gods' to Score. 
        # But 'Ten Gods' are dynamic relationships (DayMaster vs Element).
        # A static linear model on [Wood, Fire...] CANNOT represent "Officer" 
        # unless we know the DayMaster. 
        #
        # Hack solution for Cold Start:
        # We save a special 'RuleBasedModel' wrapper instead of a raw sklearn model.
        
        class RuleBasedModel:
            def __init__(self, vectorizer_instance, aspect_weights):
                self.vec = vectorizer_instance
                self.weights = aspect_weights
                
            def predict(self, X):
                # X is typically a list of vectors. But we need the original chart to do logic!
                # This breaks the sklearn pattern where predict takes X.
                # However, for our app, we can make 'X' contain the calculation result of Ten Gods?
                # No, X is just numbers.
                
                # BETTER: The 'vectorize_chart' logic should probably be called by the model 
                # wrapper if we want rule-logic.
                # But to fit the sklearn API, we assume X is rich.
                #
                # Fallback: We will generate 100 synthetic charts, 
                # calculate their 'Physics Score' using calculate_ten_gods_strength + weights,
                # and then TRAIN the SVR on this synthetic data!
                return np.zeros(len(X)) # Placeholder
                
        # Generate Synthetic Data
        print("  -> Generative: Simulating 50 synthetic destinies...")
        X_synth = []
        y_synth = []
        
        import random
        stems = self.vectorizer.stems
        branches = self.vectorizer.branches
        
        for _ in range(50):
            # Random Chart
            chart = {
                "year": {"stem": random.choice(stems), "branch": random.choice(branches)},
                "month": {"stem": random.choice(stems), "branch": random.choice(branches)},
                "day": {"stem": random.choice(stems), "branch": random.choice(branches)},
                "hour": {"stem": random.choice(stems), "branch": random.choice(branches)},
            }
            
            # Calculate Physics Score (Ground Truth Proxy)
            gods = self.vectorizer.calculate_ten_gods_strength(chart)
            
            # Weighted Sum for Aspect (e.g. Career)
            # score = Sum(W * GodStrength)
            # Default to Career Weights for now
            w_map = self.vectorizer.W_CAREER
            score = 0
            for god, strength in gods.items():
                w = w_map.get(god, 0)
                score += w * strength
            
            # Scaling to 0-100 logic (Strength is roughly 0-20)
            final_score = min(score * 10, 100) # Arbitrary scaling
            
            vec = self.vectorizer.vectorize_chart(chart)
            X_synth.append(vec)
            y_synth.append(final_score)
            
        X_synth = np.array(X_synth)
        y_synth = np.array(y_synth)
        
        # Train SVR on Synthetic Data
        model = SVR(kernel='rbf', C=100, gamma='scale', epsilon=0.1)
        model.fit(X_synth, y_synth)
        
        print(f"  -> Cold Start Model Trained on {len(X_synth)} synthetic cases.")
        self._save_model(model, aspect)
        return True

    def _save_model(self, model, aspect):
        model_path = os.path.join(self.model_dir, f"model_{aspect}.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
        print(f"✅ Model saved to: {model_path}")


    def _load_model_safe(self, aspect):
        model_path = os.path.join(self.model_dir, f"model_{aspect}.pkl")
        if not os.path.exists(model_path):
            return None
        with open(model_path, "rb") as f:
            return pickle.load(f)

    def predict(self, chart_data, aspect="wealth"):
        """
        Predicts score for a new chart.
        """
        model = self._load_model_safe(aspect)
        if not model:
            print(f"No model found for {aspect}. Please train first.")
            return None

        # Vectorize
        # Note: Vectorizer must be stateless or consistent with training
        vec = self.vectorizer.vectorize_chart(chart_data)
        X_new = np.array([vec])
        
        pred = model.predict(X_new)
        return pred[0]

if __name__ == "__main__":
    # Test Run
    trainer = ModelTrainer()
    # Attempt classification if sufficient data exists
    # For now, we likely have few cases, so results might be poor.
    trainer.train(aspect="wealth", algorithm="svm")
