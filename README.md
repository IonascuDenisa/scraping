# 🐾 Thrive Petcare Scraper
This project extracts the number of available appointment time slots for each doctor and date from [Thrive Petcare](https://www.thrivepetcare.com).
- Python 3.12
- Scrapy framework
- Output: CSV or JSON

## 🔍 Initial Site Analysis & Access Issues
My first interaction with the website resulted in a block message:
“_You have been blocked. You are unable to access this website._”.

To bypass this restriction, I initially tried several VPNs from Europe. While they worked temporarily,
I was repeatedly blocked after a few minutes. Switching to a VPN based in the US proved to be a stable and reliable solution.

Once I gained consistent access to the site, I began exploring its structure and user flow to understand how users interact with the platform. 
I noticed that the site automatically suggested nearby veterinary clinics based on the user's location. Since my VPN location changed periodically,
the recommended clinics varied accordingly.

To avoid this inconsistency and find a more stable way to access the full list of locations, I searched for a central directory page. That’s how I discovered:
https://www.thrivepetcare.com/m/all-locations — a page that lists all veterinary centers across the U.S., organized by state and city

> 💡 **Observation:** Not all clinics listed on the site support online booking — some pages don’t display the “Book Online” button.

#### 📄 Form Page Analysis
After completing the initial form with information about the pet, the user is redirected to a dynamic appointment scheduling page. I manually explored several clinic pages 
at random and noticed that the layout and behavior differed between clinics — some displayed the names of available doctors, while others did not.

Initially, I inspected the page source to find available appointment times, but they were not present in the HTML. I then searched for doctor names and was able to find them directly in the source. 
From that point forward, I relied exclusively on **Chrome DevTools** to inspect network traffic.

In the Network tab, I discovered multiple API requests to: _https://www.thrivepetcare.com/api_  .The appointment data was spread across several separate requests, unfortunately, there was no single endpoint that returned all of this information in one payload.

## 🧩 Challenges & Observations

> ⚠️ **The hardest part of the project was reverse-engineering the correct call sequence**  
> Each endpoint depends on values returned by the previous one, forming a strict dependency chain.

## 🔗 API Flow Breakdown

### 👟 Step 1 – Extract `location_id` from All Locations Page
The starting point is the HTML page https://www.thrivepetcare.com/all-locations

- This page returns an HTML document containing a `<script>` tag with embedded JSON.
- Using **XPath**, the embedded JSON is extracted and parsed.
- Each location entry in the JSON contains a `location_id` which is required for all subsequent API calls.
> 💡 This step requires HTML parsing, not a direct API request.

### 👟 Step 2 – Get `appointment_type_id`

Once a `location_id` is known, this endpoint returns the types of appointments available for that location (e.g., wellness, illness).

```http
GET https://www.thrivepetcare.com/api/booking/v1/appointments/{location_id}/types-statuses?showOnlyForOnlineBooking=true
```
- Input: location_id
- extracted: A list of appointment_type_ids
- Only appointment types that can be booked online are returned

### 👟 Step 3 – Get Available Dates `date`
For a given location and appointment type, this endpoint provides all the available dates for booking.
```http
GET https://www.thrivepetcare.com/api/booking/v1/locations/{location_id}/available-dates?appointmentTypeId={appointment_type_id}
```
- Inputs: location_id, appointment_type_id
- extracted: List of dates with a hasAvailableTime flag
  `available_dates = ['2025-07-08', '2025-07-09', '2025-07-11', ...]`
  

### 👟 Step 4 – Get `provider_id` (Doctors)
This endpoint returns the doctors with availability on a specific date for a specific appointment type.
```http
GET https://www.thrivepetcare.com/api/booking/v1/locations/{location_id}/providers-schedule?selectedDate={date}&onlyActive=true&vetOnly=true&appointmentTypeId={appointment_type_id}
```
- Inputs: location_id, appointment_type_id, date
- extracted: List of providers 


### 👟 Step 5 – Get Available Time Slots
The final step retrieves the actual time slots available for a selected doctor on a given day.
```http
GET https://www.thrivepetcare.com/api/booking/v2/{location_id}/availabletimes/{appointment_type_id}/{date}?providerId={provider_id}
```
- Inputs: location_id, appointment_type_id, date, provider_id
- extracted: List of time slot strings (e.g., "09:00", "09:30")
<br>
⏱️ Note: Not all returned time slots are available. Each slot includes a status field, and we only keep those where: "status": "Available"
 The time interval between slots may vary depending on the appointment type.

For example:
- "Illness" appointments are typically 30 minutes apart
- "Wellness" appointments may be scheduled every 15 minutes<br>
This means that the structure and number of time slots per day differ depending on the type of visit being scheduled.



