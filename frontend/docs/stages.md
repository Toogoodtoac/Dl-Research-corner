## **Webapp Setup Instructions**

### **Prerequisites**

- Python 3.11+ with virtual environment activated
- Node.js 18+ and pnpm installed
- Google Drive Desktop synced to `/Users/tranlynhathao/Library/CloudStorage/GoogleDrive-haotran04022005@gmail.com/.shortcut-targets-by-id/1fXA9wu7HLdKxI0-yJ-n66eq2JV0d6j-H/AIC2025_data`

---

## **Option 1: Local Data Only (Development)**

### **Step 1: Set Environment**

```bash
export AIC_ENV=dev
```

### **Step 2: Start Backend**

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Step 3: Start Frontend**

```bash
cd frontend
pnpm dev
```

### **What You Get:**

- **FAISS Indexes**: Local (CLIP + LongCLIP)
- **Features**: Local features-longclip
- **Raw Data**: Keyframes_L21, Keyframes_L22 only
- **Performance**: Fast (local storage)
- **Data Coverage**: Limited (2 datasets)

---

## **Option 2: Google Drive + Local Hybrid (Recommended for Competitions)**

### **Step 1: Set Environment**

```bash
export AIC_ENV=prod
```

### **Step 2: Start Backend**

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Step 3: Start Frontend**

```bash
cd frontend
pnpm dev
```

### **✅ What You Get:**

- **FAISS Indexes**: Local (fast performance)
- **Features**: Local (fast performance)
- **Raw Data**: Google Drive (Keyframes_L21 through L30)
- **Performance**: Fast indexes + comprehensive data
- **Data Coverage**: Full (10 datasets)

---

## **Option 3: Full Google Drive (Maximum Data)**

### **Step 1: Copy Google Drive Indexes (One-time setup)**

```bash
# Create indexes directory in Google Drive
mkdir -p "/Users/tranlynhathao/Library/CloudStorage/GoogleDrive-haotran04022005@gmail.com/.shortcut-targets-by-id/1fXA9wu7HLdKxI0-yJ-n66eq2JV0d6j-H/AIC2025_data/indexes/faiss"

# Copy local indexes to Google Drive for backup
cp data/indexes/faiss/* "/Users/tranlynhathao/Library/CloudStorage/GoogleDrive-haotran04022005@gmail.com/.shortcut-targets-by-id/1fXA9wu7HLdKxI0-yJ-n66eq2JV0d6j-H/AIC2025_data/indexes/faiss/"
```

### **Step 2: Set Environment**

```bash
export AIC_ENV=prod
```

### **Step 3: Start Services**

```bash
# Backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in new terminal)
cd frontend
pnpm dev
```

---

## **Environment Variables Reference**

| Variable | Value | Description |
|----------|-------|-------------|
| `AIC_ENV` | `dev` | Use local data only |
| `AIC_ENV` | `prod` | Use Google Drive + local hybrid |
| `AIC_ENV` | `colab` | Use Google Drive only |

---

## **Troubleshooting**

### **Issue: "No data sources available"**

```bash
# Check Google Drive sync status
ls -la "/Users/tranlynhathao/Library/CloudStorage/GoogleDrive-haotran04022005@gmail.com/.shortcut-targets-by-id/1fXA9wu7HLdKxI0-yJ-n66eq2JV0d6j-H/AIC2025_data"

# Verify environment variable
echo $AIC_ENV
```

### **Issue: "FAISS indexes not found"**

```bash
# Verify local indexes exist
ls -la data/indexes/faiss/

# Check file permissions
chmod 644 data/indexes/faiss/*
```

### **Issue: "Search returning wrong results"**

```bash
# Run validation script
python scripts/validate_data_sources.py

# Check if features are corrupted
python scripts/debug_faiss_index.py
```

---

## **Recommended Setup for Your Use Case**

Since you're doing team competitions and need comprehensive data coverage, I recommend:

```bash
# 1. Set environment to production (uses Google Drive)
export AIC_ENV=prod

# 2. Start backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. Start frontend (in new terminal)
cd frontend
pnpm dev
```

This gives you:

- ✅ **Fast local FAISS indexes** for performance
- ✅ **Comprehensive Google Drive data** (L21-L30)
- ✅ **Best of both worlds** for competitions
