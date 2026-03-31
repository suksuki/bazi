import streamlit as st
import pandas as pd
import json
import numpy as np
import time
from learning.db import LearningDB
from core.vectorizer import Vectorizer

def render_training_center():
    st.header("🏋️ 量子权重训练场 (Quantum Weights Trainer)")
    st.caption("Auto-tune Vectorizer weights using 'Deep Mining' cases.")

    db = LearningDB()
    vec = Vectorizer(use_db_weights=True) # Load latest trained weights
    
    # 1. Load Data
    cases = db.get_all_cases()
    if not cases:
        st.warning("⚠️ No training cases found. Use 'Deep Mining' to extract cases from books/videos.")
        return

    st.subheader(f"📚 训练数据集 (N={len(cases)})")
    
    # Eval Function
    def evaluate_model(vectorizer, case_list):
        total_error = 0.0
        details = []
        valid_count = 0
        
        for c in case_list:
            # 1. Ground Truth
            truth = c.get('truth', {})
            # Normalized truth to 0-100 if needed (assuming already 0-100)
            
            # 2. Prediction
            try:
                pred = vectorizer.calculate_aspects(c['chart'])
            except Exception as e:
                continue

            # 3. Calculate Error (MAE)
            case_err = 0.0
            aspect_count = 0
            
            # Compare key keys
            keys_to_compare = ['wealth', 'career', 'marriage', 'health']
            
            row_data = {"Name": c['name']}
            
            for k in keys_to_compare:
                if k in truth:
                    t_val = float(truth[k])
                    p_val = pred.get(k, 50.0) # Default neutral if missing prediction
                    diff = abs(t_val - p_val)
                    case_err += diff
                    aspect_count += 1
                    
                    row_data[f"{k.title()} (T)"] = t_val
                    row_data[f"{k.title()} (P)"] = round(p_val, 1)
                    
            if aspect_count > 0:
                mean_case_err = case_err / aspect_count
                total_error += mean_case_err
                valid_count += 1
                row_data["Mean Error"] = round(mean_case_err, 2)
                details.append(row_data)
        
        global_mae = total_error / valid_count if valid_count > 0 else 999.0
        return global_mae, pd.DataFrame(details)

    # Initial Eval
    mae, df_details = evaluate_model(vec, cases)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Global MAE (Mean Error)", f"{mae:.2f}", delta_color="inverse")
    col2.metric("Active Weights", f"{len(vec.W_E) + len(vec.W_CAREER)}")
    col3.metric("Training Cases", f"{len(cases)}")
    
    with st.expander("📊 查看具体差异 (Predictions vs Truth)", expanded=False):
        st.dataframe(df_details, width="stretch")

    st.divider()
    
    # 2. Training Controls
    st.subheader("⚙️ 随机梯度优化 (Stochastic Optimization)")
    
    c_train1, c_train2 = st.columns([1, 2])
    
    with c_train1:
        iterations = st.number_input("Iterations", 10, 500, 50)
        learning_rate = st.slider("Learning Rate", 0.01, 0.5, 0.1)
        
    with c_train2:
        st.write(" ")
        st.write(" ")
        start_opt = st.button("🚀 开始训练 (Start Optimization)", type="primary")

    if start_opt:
        curr_weights = {
            "W_E": vec.W_E.copy(),
            "W_CAREER": vec.W_CAREER.copy()
        }
        
        best_loss = mae
        best_weights = curr_weights
        
        progress_bar = st.progress(0)
        chart_loss = st.empty()
        loss_history = [mae]
        
        st.toast(f"Starting training loop... Baseline Loss: {mae:.2f}")
        
        for i in range(iterations):
            # 1. Jitter Weights
            test_weights = {
                "W_E": best_weights["W_E"].copy(),
                "W_CAREER": best_weights["W_CAREER"].copy()
            }
            
            # Mutate W_E
            for k in test_weights["W_E"]:
                if np.random.rand() < 0.3: # 30% chance to mutate each weight
                    noise = (np.random.rand() - 0.5) * learning_rate * 5.0 # +/- change
                    test_weights["W_E"][k] = max(0.1, test_weights["W_E"][k] + noise)
            
            # Mutate W_CAREER
            for k in test_weights["W_CAREER"]:
                 if np.random.rand() < 0.3:
                    noise = (np.random.rand() - 0.5) * learning_rate * 0.5
                    test_weights["W_CAREER"][k] = max(0.01, test_weights["W_CAREER"][k] + noise)

            # 2. Update Vectorizer
            vec.update_weights(test_weights)
            
            # 3. Eval
            new_loss, _ = evaluate_model(vec, cases)
            
            # 4. Accept if better
            if new_loss < best_loss:
                best_loss = new_loss
                best_weights = test_weights
                st.toast(f"Is better! Loss: {best_loss:.2f}")
            
            loss_history.append(best_loss)
            chart_loss.line_chart(loss_history)
            progress_bar.progress((i+1)/iterations)
            time.sleep(0.05) # UI update
            
        # End loop
        st.success(f"Training Complete! Optimized Loss: {best_loss:.2f} (Improvement: {mae - best_loss:.2f})")
        
        # Save
        db.save_weights(best_weights, best_loss, note=f"Auto-trained on {len(cases)} cases")
        st.info("✅ Weights saved to BrainDB. They will be auto-loaded next time.")
        
        # Reload interface
        time.sleep(2)
        st.rerun()
