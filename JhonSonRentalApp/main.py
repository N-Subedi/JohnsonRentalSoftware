import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QComboBox,
                            QMessageBox, QListWidget, QDateEdit, QFormLayout, QLineEdit, QHBoxLayout, QListWidgetItem, QTextEdit)
from PyQt5.QtCore import QDate
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime, timedelta


# Initialize Firebase
cred = credentials.Certificate('carrentalapp-be7b1-firebase-adminsdk-ehghs-0e878ec2dc.json')
initialize_app(cred)
db = firestore.client()


def update_existing_reservations():
   try:
       # Define rental charges for car types
       rental_charges = {
           "Sedan": 50,      # $50 per day
           "SUV": 70,        # $70 per day
           "Pick-up": 60,    # $60 per day
           "Van": 80         # $80 per day
       }


       # Get all reservations from Firestore
       reservations = db.collection('Reservations').get()
       for res in reservations:
           res_data = res.to_dict()
           car_type = res_data.get('car_type')
           check_out_date_str = res_data.get('check_out_date')
           return_date_str = res_data.get('return_date')


           # Skip reservations with missing fields
           if not car_type or not check_out_date_str or not return_date_str:
               continue


           # Parse dates, handle multiple formats
           try:
               check_out_date = datetime.strptime(check_out_date_str, '%Y-%m-%d').date()
           except ValueError:
               check_out_date = datetime.strptime(check_out_date_str, '%Y/%m/%d').date()


           try:
               return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
           except ValueError:
               return_date = datetime.strptime(return_date_str, '%Y/%m/%d').date()


           # Calculate rental duration
           rental_days = (return_date - check_out_date).days


           # Calculate rental charge
           daily_rate = rental_charges.get(car_type, 0)
           total_charge = daily_rate * rental_days


           # Apply discount for rentals of a week or longer (10% discount)
           if rental_days >= 7:
               total_charge *= 0.9


           # Update Firestore document with total charge
           db.collection('Reservations').document(res.id).update({
               'total_charge': round(total_charge, 2)  # Round to 2 decimal places
           })


       print("All reservations updated successfully!")


   except Exception as e:
       print(f"An error occurred: {e}")






class MainApp(QWidget):
   def __init__(self):
       super().__init__()


       # Automatically update existing reservations when the app starts
       update_existing_reservations()


       # Set up the window
       self.setWindowTitle("Car Rental System - Main Menu")
       self.setGeometry(100, 100, 400, 400)


       # Create layout
       layout = QVBoxLayout()


       # Create Reservations Button
       self.create_reservation_button = QPushButton("Create Reservation")
       self.create_reservation_button.clicked.connect(self.open_create_reservation)
       layout.addWidget(self.create_reservation_button)


       # View Reservations Button
       self.view_reservations_button = QPushButton("View Reservations")
       self.view_reservations_button.clicked.connect(self.open_view_reservations)
       layout.addWidget(self.view_reservations_button)


       # Manager View Button
       self.manager_view_button = QPushButton("Manager View")
       self.manager_view_button.clicked.connect(self.open_manager_view)
       layout.addWidget(self.manager_view_button)


       # Extend Reservation Button
       self.extend_reservation_button = QPushButton("Extend Reservation")
       self.extend_reservation_button.clicked.connect(self.open_extend_reservation)
       layout.addWidget(self.extend_reservation_button)


       # Set the layout
       self.setLayout(layout)


   # Methods to handle button actions
   def open_create_reservation(self):
       self.create_reservation_window = CreateReservationForm(self)
       self.create_reservation_window.show()


   def open_view_reservations(self):
       self.view_reservations_window = ViewReservationsWindow(self)
       self.view_reservations_window.show()


   def open_manager_view(self):
       self.manager_view_window = ManagerViewWindow(self)
       self.manager_view_window.show()


   def open_extend_reservation(self):
       self.extend_reservation_window = ExtendReservationWindow(self)
       self.extend_reservation_window.show()




# Create Reservation Form
class CreateReservationForm(QWidget):
   def __init__(self, parent):
       super().__init__()


       # Set up the window
       self.setWindowTitle("Car Rental Reservation Form")
       self.setGeometry(100, 100, 400, 400)
       self.parent = parent


       # Create layout
       layout = QFormLayout()


       # Driver Name
       self.driver_name_label = QLabel("Driver Name:")
       self.driver_name_input = QLineEdit()
       layout.addRow(self.driver_name_label, self.driver_name_input)


       # Car Type
       self.car_type_label = QLabel("Car Type:")
       self.car_type_combo = QComboBox()
       self.car_type_combo.addItems(["Sedan", "SUV", "Pick-up", "Van"])
       layout.addRow(self.car_type_label, self.car_type_combo)


       # Reservation Date (with calendar)
       self.reservation_date_label = QLabel("Reservation Date:")
       self.reservation_date_input = QDateEdit()
       self.reservation_date_input.setCalendarPopup(True)
       self.reservation_date_input.setMinimumDate(QDate.currentDate().addDays(1))  # Reservation must be at least 24 hours in advance
       layout.addRow(self.reservation_date_label, self.reservation_date_input)


       # Check-out Date (with calendar)
       self.check_out_date_label = QLabel("Check-out Date:")
       self.check_out_date_input = QDateEdit()
       self.check_out_date_input.setCalendarPopup(True)
       self.check_out_date_input.setMinimumDate(QDate.currentDate().addDays(1))
       layout.addRow(self.check_out_date_label, self.check_out_date_input)


       # Return Date (with calendar)
       self.return_date_label = QLabel("Return Date:")
       self.return_date_input = QDateEdit()
       self.return_date_input.setCalendarPopup(True)
       self.return_date_input.setMinimumDate(QDate.currentDate().addDays(2))  # At least a day after the check-out date
       layout.addRow(self.return_date_label, self.return_date_input)


       # Submit Button
       self.submit_button = QPushButton("Submit Reservation")
       self.submit_button.clicked.connect(self.submit_reservation)
       layout.addRow(self.submit_button)


       # Home Screen Button
       self.home_button = QPushButton("Home Screen")
       self.home_button.clicked.connect(self.go_home)
       layout.addRow(self.home_button)


       # Set the layout
       self.setLayout(layout)


   def submit_reservation(self):
       # Collect input data
       driver_name = self.driver_name_input.text().strip()
       car_type = self.car_type_combo.currentText()
       reservation_date = self.reservation_date_input.date().toPyDate()
       check_out_date = self.check_out_date_input.date().toPyDate()
       return_date = self.return_date_input.date().toPyDate()


       # Validate inputs
       if not driver_name:
           QMessageBox.warning(self, "Input Error", "Please fill in the driver's name.")
           return


       # Ensure the dates follow proper logic
       if reservation_date < datetime.now().date() + timedelta(days=1):
           QMessageBox.warning(self, "Date Error", "Reservation date must be at least 24 hours in advance.")
           return


       if check_out_date <= reservation_date:
           QMessageBox.warning(self, "Date Error", "Check-out date must be after the reservation date.")
           return


       if return_date <= check_out_date:
           QMessageBox.warning(self, "Date Error", "Return date must be after the check-out date.")
           return


       # Calculate rental duration
       rental_days = (return_date - check_out_date).days


       # Define rental charges for car types
       rental_charges = {
           "Sedan": 50,  # $50 per day
           "SUV": 70,  # $70 per day
           "Pick-up": 60,  # $60 per day
           "Van": 80  # $80 per day
       }


       # Calculate rental charge
       daily_rate = rental_charges.get(car_type)
       total_charge = daily_rate * rental_days


       # Apply discount for rentals of a week or longer (10% discount)
       if rental_days >= 7:
           total_charge *= 0.9


       # Store reservation data in Firestore
       reservation_data = {
           'driver_name': driver_name,
           'car_type': car_type,
           'reservation_date': reservation_date.strftime('%Y-%m-%d'),
           'check_out_date': check_out_date.strftime('%Y-%m-%d'),
           'return_date': return_date.strftime('%Y-%m-%d'),
           'total_charge': round(total_charge, 2),
           'extension_requested': False,
           'manager_approved': False  # Adding a field for manager approval
       }


       try:
           db.collection('Reservations').add(reservation_data)
           QMessageBox.information(self, "Success",
                                   f"Reservation submitted successfully! Total charge: ${total_charge:.2f}")
           # Clear the form after submission
           self.driver_name_input.clear()
           self.reservation_date_input.setDate(QDate.currentDate().addDays(1))
           self.check_out_date_input.setDate(QDate.currentDate().addDays(1))
           self.return_date_input.setDate(QDate.currentDate().addDays(2))
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def go_home(self):
       self.close()
       self.parent.show()


# View Reservations Window
class ViewReservationsWindow(QWidget):
   def __init__(self, parent):
       super().__init__()


       # Set up the window
       self.setWindowTitle("View Reservations")
       self.setGeometry(100, 100, 500, 500)
       self.parent = parent


       # Create layout
       layout = QVBoxLayout()


       # Title
       title = QLabel("Current Reservations")
       layout.addWidget(title)


       # List Widget to display reservations
       self.reservations_list = QListWidget()
       layout.addWidget(self.reservations_list)


       # Home Screen Button
       self.home_button = QPushButton("Home Screen")
       self.home_button.clicked.connect(self.go_home)
       layout.addWidget(self.home_button)


       # Load reservations
       self.load_reservations()


       # Set the layout
       self.setLayout(layout)


   def load_reservations(self):
       try:
           # Get all reservations from Firestore
           reservations = db.collection('Reservations').get()
           for res in reservations:
               data = res.to_dict()
               driver_name = data.get('driver_name', 'N/A')
               car_type = data.get('car_type', 'N/A')
               reservation_date = data.get('reservation_date', 'N/A')
               check_out_date = data.get('check_out_date', 'N/A')
               return_date = data.get('return_date', 'N/A')
               total_charge = data.get('total_charge', 'N/A')  # Retrieve total charge


               # Build the reservation display text
               reservation_text = (
                   f"Driver: {driver_name}\n"
                   f"Car Type: {car_type}\n"
                   f"Reservation Date: {reservation_date}\n"
                   f"Check-Out Date: {check_out_date}\n"
                   f"Return Date: {return_date}\n"
                   f"Total Charge: ${total_charge}\n"  # Display total charge
                   f"{'-' * 40}\n"  # Separator line
               )


               list_item = QListWidgetItem()
               list_item.setText(reservation_text)
               self.reservations_list.addItem(list_item)
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def go_home(self):
       self.close()
       self.parent.show()










# Placeholder classes for Manager View and Extend Reservation
# Manager View Window
# Manager View Window
# Manager View Window
# Manager View Window
# Manager View Window
# Manager View Window
# Manager View Window
class ManagerViewWindow(QWidget):
   def __init__(self, parent):
       super().__init__()
       self.setWindowTitle("Manager View")
       self.setGeometry(100, 100, 600, 600)
       self.parent = parent


       # Create layout
       layout = QVBoxLayout()


       # Title
       title = QLabel("Manage Reservations")
       layout.addWidget(title)


       # List Widget to display reservations
       self.reservations_list = QListWidget()
       layout.addWidget(self.reservations_list)


       # Approve Button
       self.approve_button = QPushButton("Approve Selected Reservation")
       self.approve_button.clicked.connect(self.approve_reservation)
       layout.addWidget(self.approve_button)


       # Disapprove Button
       self.disapprove_button = QPushButton("Disapprove Selected Reservation")
       self.disapprove_button.clicked.connect(self.disapprove_reservation)
       layout.addWidget(self.disapprove_button)


       # Approve Extension Button
       self.approve_extension_button = QPushButton("Approve Extension for Selected Reservation")
       self.approve_extension_button.clicked.connect(self.approve_extension)
       layout.addWidget(self.approve_extension_button)


       # Disapprove Extension Button
       self.disapprove_extension_button = QPushButton("Disapprove Extension for Selected Reservation")
       self.disapprove_extension_button.clicked.connect(self.disapprove_extension)
       layout.addWidget(self.disapprove_extension_button)


       # Delete Button
       self.delete_button = QPushButton("Delete Selected Reservation")
       self.delete_button.clicked.connect(self.delete_reservation)
       layout.addWidget(self.delete_button)


       # Home Screen Button
       self.home_button = QPushButton("Home Screen")
       self.home_button.clicked.connect(self.go_home)
       layout.addWidget(self.home_button)


       # Set the layout
       self.setLayout(layout)


       # Load reservations after layout setup
       self.load_reservations()


   def load_reservations(self):
       try:
           # Get all reservations from Firestore
           reservations = db.collection('Reservations').get()
           for res in reservations:
               data = res.to_dict()
               driver_name = data.get('driver_name', 'N/A')
               car_type = data.get('car_type', 'N/A')
               reservation_date = data.get('reservation_date', 'N/A')
               check_out_date = data.get('check_out_date', 'N/A')
               return_date = data.get('return_date', 'N/A')
               total_charge = data.get('total_charge', 'N/A')
               requested_return_date = data.get('requested_return_date', None)
               extension_requested = data.get('extension_requested', False)
               manager_approved = data.get('manager_approved', False)
               extension_approved = data.get('extension_approved', False)
               disapproved = data.get('disapproved', False)


               # Display reservation text differently if disapproved
               reservation_text = (
                   f"Driver: {driver_name} | Car Type: {car_type} | "
                   f"Date: {reservation_date} to {return_date} | "
                   f"Total Charge: ${total_charge} | "
                   f"Manager Approved: {'Yes' if manager_approved else 'No'}"
               )


               # If an extension is requested, show the requested return date
               if extension_requested and requested_return_date:
                   reservation_text += f" | Requested Extension Date: {requested_return_date}"


               # If an extension is approved, update the return date
               if extension_approved:
                   reservation_text += f" | Extension Approved: {'Yes' if extension_approved else 'No'}"


               # Mark as disapproved if applicable
               if disapproved:
                   reservation_text = f"[DISAPPROVED] {reservation_text}"


               list_item = QListWidgetItem()
               list_item.setText(reservation_text)
               list_item.setData(1000, res.id)  # Store the document ID for future reference
               self.reservations_list.addItem(list_item)
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def approve_reservation(self):
       selected_item = self.reservations_list.currentItem()
       if not selected_item:
           QMessageBox.warning(self, "Selection Error", "Please select a reservation to approve.")
           return


       reservation_id = selected_item.data(1000)
       try:
           # Update Firestore document to set manager_approved to True and disapproved to False
           db.collection('Reservations').document(reservation_id).update({'manager_approved': True, 'disapproved': False})
           QMessageBox.information(self, "Success", "Reservation approved successfully!")
           self.reservations_list.clear()
           self.load_reservations()
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def disapprove_reservation(self):
       selected_item = self.reservations_list.currentItem()
       if not selected_item:
           QMessageBox.warning(self, "Selection Error", "Please select a reservation to disapprove.")
           return


       reservation_id = selected_item.data(1000)
       try:
           # Update Firestore document to set disapproved to True and manager_approved to False
           db.collection('Reservations').document(reservation_id).update({'disapproved': True, 'manager_approved': False})
           QMessageBox.information(self, "Success", "Reservation disapproved successfully!")
           self.reservations_list.clear()
           self.load_reservations()
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def approve_extension(self):
       selected_item = self.reservations_list.currentItem()
       if not selected_item:
           QMessageBox.warning(self, "Selection Error", "Please select a reservation to approve the extension.")
           return


       reservation_id = selected_item.data(1000)
       try:
           # Update Firestore document to set return_date to requested_return_date and mark extension as approved
           res_ref = db.collection('Reservations').document(reservation_id)
           res_data = res_ref.get().to_dict()


           if 'requested_return_date' in res_data:
               new_return_date = res_data['requested_return_date']
               res_ref.update({
                   'return_date': new_return_date,
                   'extension_approved': True,
                   'extension_requested': False
               })
               QMessageBox.information(self, "Success", "Extension approved successfully!")
               self.reservations_list.clear()
               self.load_reservations()
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def disapprove_extension(self):
       selected_item = self.reservations_list.currentItem()
       if not selected_item:
           QMessageBox.warning(self, "Selection Error", "Please select a reservation to disapprove the extension.")
           return


       reservation_id = selected_item.data(1000)
       try:
           # Update Firestore document to clear requested_return_date and mark extension as not approved
           db.collection('Reservations').document(reservation_id).update({
               'requested_return_date': firestore.DELETE_FIELD,
               'extension_approved': False,
               'extension_requested': False
           })
           QMessageBox.information(self, "Success", "Extension disapproved successfully!")
           self.reservations_list.clear()
           self.load_reservations()
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def delete_reservation(self):
       selected_item = self.reservations_list.currentItem()
       if not selected_item:
           QMessageBox.warning(self, "Selection Error", "Please select a reservation to delete.")
           return


       reservation_id = selected_item.data(1000)
       try:
           # Delete Firestore document
           db.collection('Reservations').document(reservation_id).delete()
           QMessageBox.information(self, "Success", "Reservation deleted successfully!")
           self.reservations_list.clear()
           self.load_reservations()
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def go_home(self):
       self.close()
       self.parent.show()






# Extend Reservation Window
# Extend Reservation Window
class ExtendReservationWindow(QWidget):
   def __init__(self, parent):
       super().__init__()
       self.setWindowTitle("Extend Reservation")
       self.setGeometry(100, 100, 500, 500)
       self.parent = parent


       # Create layout
       layout = QVBoxLayout()


       # Title
       title = QLabel("Extend Reservation Request")
       layout.addWidget(title)


       # List Widget to display reservations eligible for extension
       self.reservations_list = QListWidget()
       layout.addWidget(self.reservations_list)


       # Load reservations
       self.load_reservations()


       # New Return Date
       self.new_return_date_label = QLabel("New Return Date:")
       self.new_return_date_input = QDateEdit()
       self.new_return_date_input.setCalendarPopup(True)
       self.new_return_date_input.setMinimumDate(QDate.currentDate().addDays(1))  # Ensure at least 1 day in the future
       layout.addWidget(self.new_return_date_label)
       layout.addWidget(self.new_return_date_input)


       # Request Extension Button
       self.request_extension_button = QPushButton("Request Extension for Selected Reservation")
       self.request_extension_button.clicked.connect(self.request_extension)
       layout.addWidget(self.request_extension_button)


       # Home Screen Button
       self.home_button = QPushButton("Home Screen")
       self.home_button.clicked.connect(self.go_home)
       layout.addWidget(self.home_button)


       # Set the layout
       self.setLayout(layout)


   def load_reservations(self):
       try:
           # Get all reservations from Firestore
           reservations = db.collection('Reservations').get()
           for res in reservations:
               data = res.to_dict()
               driver_name = data.get('driver_name', 'N/A')
               car_type = data.get('car_type', 'N/A')
               return_date = data.get('return_date', 'N/A')
               extension_requested = data.get('extension_requested', False)


               # Only show reservations that have not requested an extension yet
               if not extension_requested:
                   reservation_text = (
                       f"Driver: {driver_name} | Car Type: {car_type} | Return Date: {return_date}"
                   )
                   list_item = QListWidgetItem()
                   list_item.setText(reservation_text)
                   list_item.setData(1000, res.id)  # Store the document ID for future reference
                   self.reservations_list.addItem(list_item)
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def request_extension(self):
       selected_item = self.reservations_list.currentItem()
       if not selected_item:
           QMessageBox.warning(self, "Selection Error", "Please select a reservation to request an extension.")
           return


       new_return_date = self.new_return_date_input.date().toPyDate()
       reservation_id = selected_item.data(1000)


       try:
           # Ensure the new return date is valid
           if new_return_date <= datetime.now().date():
               QMessageBox.warning(self, "Date Error", "New return date must be in the future.")
               return


           # Update Firestore document with the new requested return date
           db.collection('Reservations').document(reservation_id).update({
               'requested_return_date': new_return_date.strftime('%Y-%m-%d'),
               'extension_requested': True,
               'extension_approved': False  # Reset approval status
           })
           QMessageBox.information(self, "Success", "Extension requested successfully!")
           self.reservations_list.clear()
           self.load_reservations()
       except Exception as e:
           QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")


   def go_home(self):
       self.close()
       self.parent.show()






if __name__ == '__main__':
   app = QApplication(sys.argv)
   window = MainApp()
   window.show()
   sys.exit(app.exec_())

