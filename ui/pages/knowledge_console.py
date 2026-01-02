"""
FDS-LKV 知识库控制台 (Knowledge Console)
========================================
全息资产管理与可视化看板

MVC 架构:
- Model: 知识库资产管理
- View: 5D 聚类可视化
- Controller: 海选触发与配置
"""

import streamlit as st
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from sklearn.decomposition import PCA

# 页面配置
st.set_page_config(
    page_title="FDS-LKV 知识库控制台",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# Model 层：数据访问
# ============================================================

class KnowledgeModel:
    """知识库数据模型"""
    
    def __init__(self):
        self._vault = None
        self._cache = None
        self._protocol_checker = None
    
    @property
    def vault(self):
        if self._vault is None:
            try:
                from core.vault_manager import get_vault_manager
                self._vault = get_vault_manager()
            except Exception as e:
                st.error(f"VaultManager 初始化失败: {e}")
        return self._vault
    
    @property
    def cache(self):
        if self._cache is None:
            try:
                from core.census_cache import get_census_cache
                self._cache = get_census_cache()
            except Exception as e:
                st.error(f"CensusCache 初始化失败: {e}")
        return self._cache
    
    def get_vault_stats(self) -> Dict:
        """获取知识库统计"""
        if not self.vault:
            return {"semantic_count": 0, "singularity_count": 0}
        return self.vault.get_vault_stats()
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        if not self.cache:
            return {"cached_patterns": 0, "total_samples": 0, "patterns": []}
        return self.cache.get_cache_stats()
    
    def get_cached_manifold(self, pattern_id: str) -> Optional[Dict]:
        """获取缓存的流形特征"""
        if not self.cache:
            return None
        return self.cache.get_cached_manifold(pattern_id)
    
    def query_semantics(self, query: str, n_results: int = 5) -> Dict:
        """语义查询"""
        if not self.vault:
            return {"ids": [], "documents": []}
        return self.vault.query_semantics(query, n_results=n_results)
    
    def fast_predict(self, bazi: Dict, tensor: List[float]) -> Dict:
        """快速预测"""
        try:
            from core.census_cache import get_fast_predictor
            predictor = get_fast_predictor()
            return predictor.predict(bazi, tensor, generate_report=True)
        except Exception as e:
            return {"error": str(e)}


# ============================================================
# View 层：可视化组件
# ============================================================

def render_header():
    """渲染页面头部"""
    st.markdown("""
    <style>
    .console-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .console-title {
        color: #00d4ff;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .console-subtitle {
        color: #8892b0;
        font-size: 0.9rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
        border: 1px solid #2d2d5a;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .stat-value {
        color: #00d4ff;
        font-size: 2rem;
        font-weight: 700;
    }
    .stat-label {
        color: #8892b0;
        font-size: 0.8rem;
    }
    </style>
    
    <div class="console-header">
        <h1 class="console-title">🧠 FDS-LKV 知识库控制台</h1>
        <p class="console-subtitle">全息资产管理与可视化看板 | Knowledge-Driven Architecture</p>
    </div>
    """, unsafe_allow_html=True)


def render_stats_bar(model: KnowledgeModel):
    """渲染统计栏"""
    vault_stats = model.get_vault_stats()
    cache_stats = model.get_cache_stats()
    
    cols = st.columns(4)
    
    with cols[0]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{vault_stats.get('semantic_count', 0)}</div>
            <div class="stat-label">语义文档</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{vault_stats.get('singularity_count', 0)}</div>
            <div class="stat-label">奇点样本</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{cache_stats.get('cached_patterns', 0)}</div>
            <div class="stat-label">缓存格局</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{cache_stats.get('total_samples', 0)}</div>
            <div class="stat-label">缓存样本</div>
        </div>
        """, unsafe_allow_html=True)


def render_5d_cluster_plot(model: KnowledgeModel, pattern_id: str):
    """渲染 5D 聚类图（PCA 降维）"""
    manifold = model.get_cached_manifold(pattern_id)
    
    if not manifold:
        st.warning(f"未找到 {pattern_id} 的缓存数据")
        return
    
    # 获取样本张量
    sample_ids = manifold.get("sample_ids", [])[:100]
    mean = manifold.get("mean_vector", [0.5] * 5)
    
    if not sample_ids:
        st.info("无样本数据")
        return
    
    # 模拟样本分布（实际应从数据库读取）
    np.random.seed(42)
    n_samples = min(100, len(sample_ids))
    cov = np.array(manifold.get("covariance", np.eye(5).tolist()))
    
    # 生成模拟数据点
    samples = np.random.multivariate_normal(mean, cov * 0.01, n_samples)
    
    # PCA 降维到 2D
    if samples.shape[0] >= 2:
        pca = PCA(n_components=2)
        samples_2d = pca.fit_transform(samples)
        
        df = pd.DataFrame({
            'PC1': samples_2d[:, 0],
            'PC2': samples_2d[:, 1],
            'E': samples[:, 0],
            'O': samples[:, 1],
            'M': samples[:, 2],
            'S': samples[:, 3],
            'R': samples[:, 4]
        })
        
        fig = px.scatter(
            df, x='PC1', y='PC2',
            color='E',
            hover_data=['E', 'O', 'M', 'S', 'R'],
            title=f'{pattern_id} 流形分布 (PCA)',
            color_continuous_scale='Viridis'
        )
        
        # 添加流形中心
        mean_2d = pca.transform([mean])
        fig.add_trace(go.Scatter(
            x=[mean_2d[0, 0]], y=[mean_2d[0, 1]],
            mode='markers',
            marker=dict(size=20, color='red', symbol='star'),
            name='流形中心 μ'
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_dimension_radar(model: KnowledgeModel, pattern_id: str):
    """渲染五维雷达图"""
    manifold = model.get_cached_manifold(pattern_id)
    
    if not manifold:
        return
    
    mean = manifold.get("mean_vector", [0.5] * 5)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=mean + [mean[0]],  # 闭合
        theta=['E (能级)', 'O (秩序)', 'M (财富)', 'S (应力)', 'R (关联)', 'E (能级)'],
        fill='toself',
        name=pattern_id,
        fillcolor='rgba(0, 212, 255, 0.3)',
        line=dict(color='#00d4ff', width=2)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1]),
            bgcolor='rgba(10, 10, 30, 0.8)'
        ),
        showlegend=False,
        template='plotly_dark',
        height=300,
        margin=dict(l=40, r=40, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_audit_simulator(model: KnowledgeModel):
    """渲染审计模拟器"""
    st.subheader("🔍 审计模拟器")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**八字配置**")
        day_master = st.selectbox("日主", ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'])
        month_branch = st.selectbox("月支", ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'])
        
        st.markdown("**5D 张量**")
        E = st.slider("E (能级)", 0.0, 1.0, 0.5)
        O = st.slider("O (秩序)", 0.0, 1.0, 0.5)
        M = st.slider("M (财富)", 0.0, 1.0, 0.3)
        S = st.slider("S (应力)", 0.0, 1.0, 0.4)
        R = st.slider("R (关联)", 0.0, 1.0, 0.4)
        
        if st.button("🚀 执行审计", use_container_width=True):
            bazi = {
                'day_master': day_master,
                'month_branch': month_branch,
                'month_main': 'zheng_guan',
                'stems': ['qi_sha'] if O > 0.4 else ['zheng_cai']
            }
            tensor = [E, O, M, S, R]
            
            with st.spinner("审计中..."):
                result = model.fast_predict(bazi, tensor)
            
            st.session_state['audit_result'] = result
    
    with col2:
        if 'audit_result' in st.session_state:
            result = st.session_state['audit_result']
            
            if 'error' in result:
                st.error(f"审计失败: {result['error']}")
            else:
                # 显示结果
                path = result.get('path', 'N/A')
                path_colors = {'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}
                
                st.markdown(f"""
                **审计结果**
                
                - 方法: `{result.get('method', 'N/A')}`
                - 路径: {path_colors.get(path, '⚪')} {path}
                - 延迟: `{result.get('latency_ms', 0):.3f} ms`
                - 格局: `{result.get('pattern_id', 'N/A')}`
                - 双轨验证: {'✅' if result.get('dual_match') else '❌'}
                """)
                
                if 'report' in result:
                    st.code(result['report'], language='text')


def render_semantic_explorer(model: KnowledgeModel):
    """渲染语义探索器"""
    st.subheader("📚 语义探索器")
    
    query = st.text_input("搜索公理", placeholder="输入关键词，如：食神格 枭神夺食")
    
    if query:
        results = model.query_semantics(query, n_results=3)
        
        if results.get("ids"):
            for i, (doc_id, doc) in enumerate(zip(results["ids"], results["documents"])):
                with st.expander(f"📄 {doc_id}", expanded=(i == 0)):
                    st.markdown(doc[:500] + "..." if len(doc) > 500 else doc)
        else:
            st.info("未找到相关文档")


# ============================================================
# Controller 层：海选控制
# ============================================================

def render_census_controller(model: KnowledgeModel):
    """渲染海选控制器"""
    st.subheader("⚙️ 海选控制器")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pattern = st.selectbox("目标格局", ["A-01", "A-02", "A-03", "B-01", "B-02", "C-01", "C-02", "D-01", "D-02"])
    
    with col2:
        limit = st.number_input("扫描限制", min_value=1000, max_value=100000, value=10000, step=1000)
    
    with col3:
        if st.button("🔍 启动海选", use_container_width=True):
            with st.spinner(f"正在海选 {pattern}..."):
                try:
                    from core.logic_compiler import get_knowledge_census
                    census = get_knowledge_census()
                    result = census.request_census(pattern, limit=limit, include_tensor=True)
                    
                    # 缓存结果
                    from core.protocol_checker import LOGIC_PROTOCOLS
                    protocol = LOGIC_PROTOCOLS.get(pattern, {})
                    model.cache.cache_census_result(
                        pattern, 
                        result['samples'], 
                        {'name': protocol.get('name', pattern)}
                    )
                    
                    st.success(f"✅ 海选完成: {result['matched_count']} / {result['total_scanned']}")
                    st.session_state['census_result'] = result
                    
                except Exception as e:
                    st.error(f"海选失败: {e}")


def render_path_config():
    """渲染路径策略配置"""
    st.subheader("🛤️ 路径策略")
    
    col1, col2 = st.columns(2)
    
    with col1:
        green_threshold = st.slider("GREEN 阈值 (D_M <)", 0.5, 3.0, 2.0, 0.1)
    
    with col2:
        yellow_threshold = st.slider("YELLOW 阈值 (D_M <)", 2.0, 5.0, 3.5, 0.1)
    
    st.info(f"GREEN: D_M < {green_threshold} | YELLOW: {green_threshold} ≤ D_M < {yellow_threshold} | RED: D_M ≥ {yellow_threshold}")


# ============================================================
# 主页面
# ============================================================

def main():
    """主函数"""
    # 初始化模型
    model = KnowledgeModel()
    
    # 渲染头部
    render_header()
    
    # 渲染统计栏
    render_stats_bar(model)
    
    st.divider()
    
    # 侧边栏：格局导航
    with st.sidebar:
        st.header("📊 格局导航")
        
        cache_stats = model.get_cache_stats()
        patterns = cache_stats.get('patterns', [])
        
        if patterns:
            selected_pattern = st.radio("选择格局", patterns, format_func=lambda x: f"📁 {x}")
        else:
            selected_pattern = None
            st.info("无缓存格局，请先执行海选")
        
        st.divider()
        
        # 路径策略配置
        render_path_config()
    
    # 主内容区
    tab1, tab2, tab3, tab4 = st.tabs(["🌌 流形可视化", "🔍 审计模拟", "📚 语义探索", "⚙️ 海选控制"])
    
    with tab1:
        if selected_pattern:
            col1, col2 = st.columns([2, 1])
            with col1:
                render_5d_cluster_plot(model, selected_pattern)
            with col2:
                render_dimension_radar(model, selected_pattern)
                
                # 显示流形信息
                manifold = model.get_cached_manifold(selected_pattern)
                if manifold:
                    st.markdown(f"""
                    **流形信息**
                    - 样本数: {manifold.get('sample_count', 0)}
                    - 丰度: {manifold.get('abundance', 0):.6f}
                    - 缓存时间: {manifold.get('cached_at', 'N/A')[:19]}
                    """)
        else:
            st.info("请先在侧边栏选择格局或执行海选")
    
    with tab2:
        render_audit_simulator(model)
    
    with tab3:
        render_semantic_explorer(model)
    
    with tab4:
        render_census_controller(model)


if __name__ == "__main__":
    main()
