from core.trainer import ModelTrainer
import sys

if __name__ == "__main__":
    
    aspect = "wealth"
    if len(sys.argv) > 1:
        aspect = sys.argv[1]
        
    print(f"🚀 Starting Antigravity Model Training for [{aspect}]...")
    
    trainer = ModelTrainer()
    
    # Try to train with SVM algorithms
    # Based on blueprint: Logic Regression / SVM
    # We use SVM (SVR) for regression capability on Vreal scores
    success = trainer.train(aspect=aspect, algorithm="svm")
    
    if success:
        print("\n✨ Training Complete! Model is ready for predictions.")
        print(f"   Model saved to: data/models/model_{aspect}.pkl")
    else:
        print("\n⚠️ Training Skipped (No Data). Using Cold Start logic (Future Feature).")
