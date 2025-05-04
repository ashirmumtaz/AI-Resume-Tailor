import streamlit as st
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from fpdf import FPDF
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from tempfile import NamedTemporaryFile
import os
from langchain_community.document_loaders import WebBaseLoader
# Set your Groq API key (use secrets or env variable in real project)
GROQ_API_KEY = "YOUR GROQ API"  # Replace this or load from env

# Streamlit App UI
st.title("📄 AI Resume Tailor (Groq + LangChain)")

resume_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])
jd_url = st.text_input("Paste Job Description URL")

if st.button("Tailor Resume") and resume_file and jd_url:
    with st.spinner("Processing..."):

        # === 1. Extract Resume Text ===
        def extract_pdf_text(file):
            doc = fitz.open(stream=file.read(), filetype="pdf")
            return "\n".join([page.get_text() for page in doc])

        resume_text = extract_pdf_text(resume_file)

        # === 2. Scrape Job Description ===
        def get_jd_text(url):
            try:
                loader = WebBaseLoader(url)
                docs = loader.load()
                return docs[0].page_content[:3000]
            except Exception as e:
                st.error("Failed to fetch job description.")
                return ""

        jd_text = get_jd_text(jd_url)

        # === 3. Call Groq LLM using LangChain ===
        def call_groq(resume, jd):
            prompt = f"""
You are an expert resume writer. Based on the job description below, tailor the resume accordingly.
Ensure it's professional, concise, ATS-friendly, and focused on aligning with the role.

Job Description:
{jd}

Original Resume:
{resume}

Return only the tailored resume text.
"""
            llm = ChatGroq(api_key=GROQ_API_KEY, model="llama3-8b-8192")
            response = llm([HumanMessage(content=prompt)])
            return response.content.strip()
        print(jd_text)
        tailored_resume_text = call_groq(resume_text, jd_text)

        # === 4. Write to PDF ===
        def text_to_pdf(text, output_path):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=11)
            for line in text.split("\n"):
                pdf.multi_cell(0, 10, line)
            pdf.output(output_path)

        tmp_pdf = NamedTemporaryFile(delete=False, suffix=".pdf")
        text_to_pdf(tailored_resume_text, tmp_pdf.name)

        # === 5. Download Button ===
        with open(tmp_pdf.name, "rb") as f:
            st.success("✅ Tailored resume text is ready!")
            st.download_button("Download Tailored Resume", f, file_name="tailored_resume.pdf")


