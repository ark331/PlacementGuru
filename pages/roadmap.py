import os, time
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import networkx as nx
import textwrap
import matplotlib.patches as mpatches
from graphviz import Digraph
import ast
from io import BytesIO

load_dotenv()
genai.configure(api_key = st.secrets["gemini"]["GEMINI_API_KEY"])
# st.sidebar.image('0')
# with st.sidebar:
#     st.image("assets\\img.png",width=300)
#     st.page_link("main.py",label="Home")
#     st.page_link("pages\\about.py",label="About")
#     st.page_link("pages\\contact.py", label="Contact")
#     st.page_link("pages\\result.py",label="Result")
#     st.page_link("pages\\chat.py",label="Chat With our AI")
#     st.page_link("pages\\roadmap.py",label="Roadmap")
    
# Create a button for search functionality
def get_roadmap_from_gemini(role, difficulty):
    prompt = (
        f"Create a career roadmap for a {role} at {difficulty} level. "
        f"Return only a Python list of tuples representing connections between steps. "
        f"Format: [(step1, step2), (step2, step3), ...]. "
        f"Keep steps concise (2-3 words max). Include 6-8 connected steps."
    )
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    # Extract the list from the response
    try:
        # Find the list in the response text using string manipulation
        start_idx = response.text.find('[')
        end_idx = response.text.find(']') + 1
        if start_idx != -1 and end_idx != -1:
            roadmap_list = ast.literal_eval(response.text[start_idx:end_idx])
            return roadmap_list
        return []
    except:
        st.error("Failed to parse the roadmap data")
        return []

def create_roadmap_graph(connections):
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add edges from connections
    G.add_edges_from(connections)
    
    # Create the figure with a larger size
    plt.figure(figsize=(15, 10))
    
    # Use a specific layout for better node distribution
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Draw the graph
    nx.draw(G, pos,
            node_color='lightblue',
            node_size=3000,
            arrowsize=20,
            edge_color='gray',
            width=2,
            with_labels=False)
    
    # Add labels with better positioning and formatting
    labels = {node: f'\n'.join(textwrap.wrap(node, width=15))
              for node in G.nodes()}
    
    nx.draw_networkx_labels(G, pos,
                           labels,
                           font_size=10,
                           font_weight='bold')
    
    # Add a title
    plt.title("Career Roadmap", pad=20, size=16)
    
    # Remove axes
    plt.axis('off')
    
    return plt

def roadmap_tab():
    st.title("Career Roadmap Generator")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        role = st.text_input("Enter your target role", placeholder="e.g., Full Stack Developer")
    with col2:
        difficulty = st.selectbox("Select difficulty level", 
                                options=["Beginner", "Intermediate", "Advanced"])
    
    if st.button("Generate Roadmap", type="primary"):
        with st.spinner("Generating your career roadmap..."):
            # Get the roadmap data
            connections = get_roadmap_from_gemini(role, difficulty)
            
            if connections:
                # Create two columns for different visualizations
                viz_col1, viz_col2 = st.columns([2, 1])
                
                with viz_col1:
                    st.subheader("Interactive Roadmap")
                    # Create and display the matplotlib graph
                    fig = create_roadmap_graph(connections)
                    st.pyplot(fig)
                
                with viz_col2:
                    st.subheader("Step-by-Step Path")
                    # Create a numbered list of steps
                    steps = set()
                    for start, end in connections:
                        steps.add(start)
                        steps.add(end)
                    
                    for i, step in enumerate(sorted(steps), 1):
                        st.markdown(f"**{i}.** {step}")
                
                # Add download button for the graph
                buf = BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                st.download_button(
                    label="Download Roadmap",
                    data=buf,
                    file_name=f"{role}_roadmap.png",
                    mime="image/png"
                )
            else:
                st.error("Failed to generate roadmap. Please try again.")

if __name__ == "__main__":
    roadmap_tab()