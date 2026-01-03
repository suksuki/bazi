import json
import numpy as np
import os

REGISTRY_FILE = "./registry/holographic_pattern/A-01.json"

def load_benchmarks():
    if not os.path.exists(REGISTRY_FILE):
        print(f"❌ Registry not found: {REGISTRY_FILE}")
        return None
    with open(REGISTRY_FILE, 'r') as f:
        data = json.load(f)
    return data['data']['benchmarks']

def simple_kmeans(data, k=2, max_iters=100):
    # 初始化：随机选择k个中心
    np.random.seed(42)  # 固定随机种子以确保可重复性
    indices = np.random.choice(len(data), k, replace=False)
    centroids = data[indices].copy()
    
    for iteration in range(max_iters):
        # 1. 分配簇
        distances = np.sqrt(((data - centroids[:, np.newaxis])**2).sum(axis=2))
        labels = np.argmin(distances, axis=0)
        
        # 2. 更新中心
        new_centroids = np.array([data[labels == i].mean(axis=0) if np.sum(labels == i) > 0 else centroids[i] for i in range(k)])
        
        # 3. 检查收敛
        if np.allclose(centroids, new_centroids, atol=1e-6):
            break
        centroids = new_centroids
        
    return centroids, labels

def analyze_profile(centroid):
    # Tensor: [E, O, M, S, R]
    e, o, m, s, r = centroid
    
    profile = []
    if o > 1.5: profile.append("High Order(官)")
    if m > 1.5: profile.append("High Wealth(财)")
    if e > 1.5: profile.append("High Energy(印/身)")
    if s < 0: profile.append("Suppressed Stress(制杀)")
    
    # 简单的自动命名推测
    name_guess = "Unknown"
    if "High Wealth(财)" in profile:
        name_guess = "Officer + Wealth (财官双美?)"
    elif "High Energy(印/身)" in profile:
        name_guess = "Officer + Seal (官印双全?)"
        
    return name_guess, profile

def main():
    print("🧪 FDS Discovery Lab: Analyzing A-01 Benchmarks...")
    
    benchmarks = load_benchmarks()
    if not benchmarks: return

    # 提取 Tensor 矩阵 (N, 5)
    tensors = np.array([b['t'] for b in benchmarks])
    print(f"   Loaded {len(tensors)} benchmarks.")
    print(f"   Tensor Mean: {np.round(np.mean(tensors, axis=0), 2)}")

    # 执行聚类
    print(f"\n🔬 Running K-Means (k=2)...")
    centroids, labels = simple_kmeans(tensors, k=2)

    # 分析结果
    print("\n📊 Cluster Analysis Report:")
    for i, center in enumerate(centroids):
        count = np.sum(labels == i)
        ratio = count / len(tensors) * 100
        
        name_guess, profile = analyze_profile(center)
        
        print(f"\n   [Cluster {i+1}] - {count} samples ({ratio:.1f}%)")
        print(f"   Centroid: {np.round(center, 2)}") # [E, O, M, S, R]
        print(f"   Features: {', '.join(profile) if profile else 'Mixed'}")
        print(f"   AI Hypothesis: {name_guess}")

    print("\n✅ Discovery Complete. These insights can now be used to define Sub-Patterns in the next Manifest version.")

if __name__ == "__main__":
    main()

