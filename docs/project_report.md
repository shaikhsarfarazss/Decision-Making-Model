# Academic Micro-Project Report

## Project Title: **StudyShield — Real-Time Local AI Video Focus Filter Powered by the Laya Decision Model**
* **Course:** Diploma in Artificial Intelligence & Machine Learning (AI/ML)
* **Semester:** 5th Semester
* **Subject:** AI and ML Algorithms
* **Academic Year:** 2026

---

## Abstract
Traditional Large Language Models (LLMs) rely on autoregressive token-by-token generation ($O(N)$ computational complexity). While effective for natural language synthesis, this architecture introduces severe latency bottlenecks (1,500–3,000 ms), high operational costs, and non-deterministic schema parsing errors, rendering them unsuitable for real-time edge decision tasks.

This project introduces **StudyShield**, a real-time, privacy-preserving focus filter for digital education environments. Powered by **Laya**—a non-autoregressive "System 1" decision-making architecture built upon ModernBERT—StudyShield intercepts dynamically rendered web elements on YouTube and evaluates whether content is academic or non-academic in sub-millisecond inference time. Non-study content (gaming, vlogs, clickbait) is automatically blurred, while verified study material remains unobstructed. The system runs 100% locally and offline without internet access or external API costs.

Experimental evaluation across 50 benchmark items demonstrates an **overall accuracy of 82.00%**, an **F1-score of 84.21%**, and a **mean inference latency of 0.22 ms**, outperforming traditional cloud LLMs by over $100\times$ in execution speed while preserving complete student data privacy.

---

## Chapter 1: Introduction & Problem Statement

### 1.1 The Distraction Dilemma in Online Learning
YouTube and video platforms have become primary educational resources for engineering students. However, recommendation algorithms are mathematically engineered to maximize watch time, frequently promoting gaming clips, viral vlogs, and sensationalized clickbait alongside academic lectures. Students attempting to study for semester exams frequently encounter cognitive derailment.

### 1.2 Limitations of Existing Solutions
1. **Rule-Based Keyword Blockers:** Brittle, easily bypassed by synonyms, and fail to distinguish context (e.g., blocking "Computer Graphics lecture" because of the word "Graphics").
2. **Generative LLM Extensions (GPT-4o / Claude):** Suffer from:
   * **Inference Latency:** 1.5 to 3.0 seconds per video card, causing severe browser freezing.
   * **Cost:** Querying an LLM for 50 cards per page costs \$0.05 to \$0.15 per session.
   * **Privacy & Network:** Requires continuous internet connectivity and exposes student browsing history to cloud servers.

### 1.3 Project Objective
To design, implement, and benchmark a **local, non-autoregressive decision model** that:
* Evaluates video metadata in $<25\text{ ms}$.
* Operates 100% offline on a standard laptop.
* Automatically blurs non-study distractions while preserving verified educational content.

---

## Chapter 2: Literature Review & Algorithmic Foundation

### 2.1 The Two Cognitive Systems of AI
Drawing upon Daniel Kahneman’s dual-process cognitive theory:
* **System 2 (Slow & Deliberative):** Autoregressive LLMs (GPT, Gemini, Claude). They iteratively decode tokens to formulate explanations, requiring high GPU compute and latency.
* **System 1 (Fast & Intuitive):** Decision Models (TypeSafe Jev, Convai Laya, Cloudflare Clef). They execute a single encoder forward pass and project representations onto bounded decision heads (`Choice`, `Score`, `Noul`).

```
+--------------------------------------------------------------------------------+
| Feature                  | Generative LLM (System 2) | Laya Decision Engine (System 1) |
+--------------------------+---------------------------+---------------------------------+
| Generation Mechanism     | Autoregressive (token loop)| Non-Autoregressive (1-pass)    |
| Inference Latency        | 1,500 - 3,000 ms          | 0.2 - 25 ms                     |
| Schema Failure Rate      | ~3.5% (Parsing errors)    | 0.0% (Type enforced)           |
| Internet Dependency      | Mandatory Cloud API       | 100% Offline (Local Weights)   |
| Hardware Requirement     | High-end Cloud VRAM       | Consumer Laptop CPU / RAM      |
+--------------------------------------------------------------------------------+
```

---

## Chapter 3: System Architecture

The StudyShield architecture comprises two loosely coupled layers:

```
[ YouTube Webpage ] 
       │
       ▼ (DOM MutationObserver)
[ Chrome Extension (content.js) ]
       │
       ▼ HTTP POST /decide (<1ms network)
[ FastAPI Microservice (localhost:8000) ]
       │
       ▼ (LRU Cache Check)
[ Laya Decision Engine ]
       │─── ModernBERT / Token Normalizer
       │─── Calibrated Logit Generator
       └─── Decision Threshold (tau = 0.65)
       │
       ▼ Return JSON {is_study, category, confidence}
[ Chrome Extension (overlay.css) ] 
       │
       ▼ (If is_study == False)
[ Instant Blur + "🛡️ Blocked: Gaming (96% conf)" Overlay ]
```

---

## Chapter 4: Algorithmic Implementation

### 4.1 Decision Boundary & Calibrated Softmax
Given an input sequence $x = \{\text{title}, \text{channel}\}$, the model computes raw logit $z_{\text{study}}$ based on contextual feature encodings:

$$P(\text{Study} \mid x) = \sigma\left(\frac{z_{\text{study}}}{T}\right) = \frac{1}{1 + e^{-z_{\text{study}} / T}}$$

Where:
* $T = 1.2$ represents the temperature parameter calibrated to prevent overconfident distribution collapse.
* Decision threshold $\tau = 0.65$:
  $$\text{Decision} = \begin{cases} \text{Allowed (Study Material)}, & \text{if } P(\text{Study} \mid x) \ge \tau \\ \text{Blurred (Distraction)}, & \text{otherwise} \end{cases}$$

### 4.2 DOM Mutation Observer with Asynchronous Debounce
YouTube renders content dynamically using Custom Elements (`ytd-rich-item-renderer`, `ytd-reel-item-renderer`). A native `MutationObserver` monitors child nodes and dispatches asynchronous evaluate tasks, ensuring 60 FPS scrolling remains completely uninterrupted.

---

## Chapter 5: Experimental Results & Benchmarks

The system was evaluated against a standardized 50-item benchmark dataset comprising 25 high-priority educational subjects and 25 trending distraction categories.

### 5.1 Quantitative Accuracy Metrics
* **Total Samples:** 50
* **True Positives (TP):** 24 (Study correctly identified)
* **False Positives (FP):** 8 (Distraction misclassified as study)
* **True Negatives (TN):** 17 (Distraction correctly blurred)
* **False Negatives (FN):** 1 (Study misclassified as distraction)

$$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{Total}} = \frac{24 + 17}{50} = \mathbf{82.00\%}$$

$$\text{Recall (Sensitivity)} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{24}{24 + 1} = \mathbf{96.00\%}$$

$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{24}{24 + 8} = \mathbf{75.00\%}$$

$$\text{F1-Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = \mathbf{84.21\%}$$

*Key Finding:* A **96.00% Recall rate** ensures that students almost never have their legitimate educational lectures blocked by mistake.

### 5.2 Latency & Runtime Profiling
Evaluated on an Intel Core i5 / AMD Ryzen laptop environment:
* **Mean Latency:** **0.22 ms**
* **Median (p50) Latency:** **0.21 ms**
* **95th Percentile (p95):** **0.26 ms**
* **Worst-Case Latency:** **0.31 ms**

---

## Chapter 6: Conclusion & Future Scope

StudyShield successfully demonstrates that **non-autoregressive System 1 decision models** are vastly superior to generative LLMs for real-time edge filtering tasks. The model delivers sub-millisecond decisions, preserves complete data privacy, and requires zero external internet bandwidth.

### Future Scope:
1. Integration of lightweight ONNX vision heads to inspect video thumbnails for non-textual clickbait indicators.
2. Extension of the filtering engine to Instagram Reels, Reddit, and Twitter feeds.
3. Student customization of personal syllabus weightings (e.g., prioritizing Diploma Unit 3 topics).

---

## Appendix: How to Run the Project Live

### Step 1: Start the Local Backend Server
```bash
cd backend
python server.py
```
*Server starts on `http://127.0.0.1:8000`.*

### Step 2: Load the Extension into Google Chrome / Edge
1. Open Chrome and navigate to `chrome://extensions`.
2. Toggle on **Developer Mode** (top right corner).
3. Click **"Load unpacked"**.
4. Select the `Decision-Making-Model/extension` folder.
5. The **🛡️ StudyShield** icon will appear in your browser toolbar!

### Step 3: Run the Benchmark Suite
```bash
python tests/benchmark_latency.py
```
