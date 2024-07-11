from fetchccalendlyinfo import fetch_appointments
from bookapointment import book_calendar

if __name__ == "__main__":
    appointment_details_list = fetch_appointments()
    if appointment_details_list:
        book_calendar(appointment_details_list)
