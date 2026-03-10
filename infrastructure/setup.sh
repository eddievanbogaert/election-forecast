#!/usr/bin/env bash
# ============================================================================
# GCP Infrastructure Setup — Election Forecast
#
# Prerequisites:
#   gcloud CLI installed and authenticated (gcloud auth login)
#   PROJECT_ID set below or passed as first argument
#
# What this script does:
#   1. Enables required GCP APIs
#   2. Creates an Artifact Registry repository for Docker images
#   3. Creates a Cloud Run service for the backend (initially no image)
#   4. Grants Firebase Hosting + Cloud Run permissions
#   5. Initialises Firebase Hosting configuration
#
# Usage:
#   chmod +x infrastructure/setup.sh
#   ./infrastructure/setup.sh
# ============================================================================

set -euo pipefail

PROJECT_ID="${1:-election-forecast-489820}"
REGION="us-central1"
SERVICE_NAME="election-forecast-api"
REPO_NAME="election-forecast"
FIREBASE_SITE="${PROJECT_ID}"

echo "==> Using GCP project: ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}"

# ── 1. Enable APIs ─────────────────────────────────────────────────────────────
echo "==> Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  firebase.googleapis.com \
  firebasehosting.googleapis.com \
  iam.googleapis.com \
  --project="${PROJECT_ID}"

# ── 2. Artifact Registry ───────────────────────────────────────────────────────
echo "==> Creating Artifact Registry repository..."
gcloud artifacts repositories create "${REPO_NAME}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="Election Forecast Docker images" \
  --project="${PROJECT_ID}" \
  2>/dev/null || echo "    (repository already exists, skipping)"

# ── 3. Service Account for GitHub Actions ─────────────────────────────────────
SA_NAME="github-actions-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Creating service account: ${SA_EMAIL}"
gcloud iam service-accounts create "${SA_NAME}" \
  --display-name="GitHub Actions deployment SA" \
  --project="${PROJECT_ID}" \
  2>/dev/null || echo "    (service account already exists, skipping)"

echo "==> Granting Cloud Run Admin to service account..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin" \
  --condition=None

echo "==> Granting Artifact Registry Writer to service account..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer" \
  --condition=None

echo "==> Granting Service Account User to service account..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None

echo "==> Granting Firebase Hosting Admin to service account..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/firebasehosting.admin" \
  --condition=None

# ── 4. Create SA key for GitHub Actions ───────────────────────────────────────
KEY_FILE="/tmp/github-actions-sa-key.json"
echo "==> Creating SA key (will be printed; add to GitHub Secrets as GCP_SA_KEY)..."
gcloud iam service-accounts keys create "${KEY_FILE}" \
  --iam-account="${SA_EMAIL}" \
  --project="${PROJECT_ID}"
echo ""
echo "============================== SA KEY =============================="
cat "${KEY_FILE}"
echo ""
echo "===================================================================="
echo "  Add the above JSON as a GitHub secret named: GCP_SA_KEY"
echo "  Then delete ${KEY_FILE}"
echo "===================================================================="

# ── 5. Initial Cloud Run placeholder deployment ────────────────────────────────
# Cloud Run requires at least one image to create the service.
# We use a public hello-world image as placeholder; CI/CD will replace it.
echo "==> Creating placeholder Cloud Run service..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="gcr.io/cloudrun/hello" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --timeout=30 \
  --project="${PROJECT_ID}" \
  2>/dev/null || echo "    (service may already exist; CI/CD will update it)"

echo ""
echo "==> Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add GCP_SA_KEY to GitHub repo secrets (Settings → Secrets → Actions)"
echo "  2. Run: firebase login && firebase init hosting --project ${PROJECT_ID}"
echo "  3. Add FIREBASE_SERVICE_ACCOUNT to GitHub secrets (from firebase-adminsdk)"
echo "  4. Push to main branch to trigger the first deploy"
echo ""
echo "Cloud Run service URL:"
gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)" 2>/dev/null || true
