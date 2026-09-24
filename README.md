# No Helmet No Green Light

AI helmet detection + simulated e-challan + PostgreSQL + Streamlit dashboard.

## Setup
1. Put your `AdvHelmet.pt` in the project root.
2. Create PostgreSQL database `traffic_ai`.
3. Run `schema.sql` in pgAdmin.
4. Copy `.env.example` to `.env` and set your PostgreSQL password.
5. Install:
   `python -m venv venv`
   `.env\Scripts\Activate.ps1`
   `pip install -r requirements.txt`
6. Test: `python test_db.py`
7. Put up to 10 MP4 videos in `videos/`.
8. Run: `python main.py`
9. Dashboard: `streamlit run dashboard.py`

## Accuracy
Edit `evaluation/ground_truth.csv` with manually verified labels, then run `python evaluate_accuracy.py`.

## Important
The e-challan/fine is simulated for an educational prototype. No real money is deducted. Twilio and OCR are optional.
