class Person:
    def __init__(self):
        self.recordType = "E"
        self.firstName = " "
        self.middleName = " "
        self.lastName = " "
        self.fullName = " "
        self.suffix = " "
        self.formerLastName = " "
        self.employeeID = " "
        self.employeeNumber = " "
        self.supervisorName = " "
        self.SSN = " "
        self.companyCode = " "
        self.companyName = " "
        self.jobTitle = " "
        self.status = " "
        self.payType = " "
        self.salaryCode = " "
        self.hourlyPayRate = 0.0
        self.salaryPayRate = 0.0
        self.payFrequency = " "
        self.flsaStatus = " "
        self.employmentEffectiveDate = " "
        self.employmentType = " "
        self.emailAddress = " "
        self.emailAddressAlt = " "
        self.phoneNumber = " "
        self.dateOfBirth = " "
        self.originalHireDate = " "
        self.lastAdjustedHireDate = " "
        self.scheduledWorkHours = " "
        self.terminationDate = " "
        self.employmentStatusStartDate = " "
        self.statusExpectedEndDate = " "
        self.custom1 = " "
        self.custom2 = " "
        self.custom3 = " "
        self.custom4 = " "
        self.custom5 = " "

    def employmentStatusFull(self):
        if self.status == "A" or self.status == "ACTIVE":
            return "Active"
        elif self.status == "T" or self.status == "INACTIVE":
            return "Terminated"
        
        return ""

    def getSalaryOrHourlyRate(self):
        if self.salaryCode == "H" or self.salaryCode == "HOUR":
            return self.hourlyPayRate
        elif self.salaryCode == "S" or self.salaryCode == "YEAR":
            return self.salaryPayRate

        return ""

    def activeStatus(self):
        if self.status == "A" or self.status == "ACTIVE":
            return "Y"
        elif self.status == "T" or self.status == "INACTIVE":
            return "N"
    
    def setPayType(self):
        if self.salaryCode == "HOUR":
            self.payType = "H"
        elif self.salaryCode == "YEAR":
            self.payType = "S"

    def setPayRate(self, pay_rate):
        if self.salaryCode == "HOUR":
            self.hourlyPayRate = pay_rate
            self.salaryPayRate = self.hourlyPayRate * 40 * 52
        elif self.salaryCode == "YEAR":
            self.salaryPayRate = pay_rate
            self.hourlyPayRate = self.hourlyPayRate / 40 / 52

    def employeeNumberCompanyCode(self):
        return self.employeeNumber + self.companyCode
        
    def print(self):
        print("Record Type: ", self.recordType)
        print("Fist Name: ", self.firstName)
        print("Middle Name:" ,self.middleName)
        print("Last Name: ", self.lastName)
        print("Full Name: ", self.fullName)
        print("Suffix: ", self.suffix)
        print("Former Last Name: ", self.formerLastName)
        print("Employee ID: ", self.employeeID)
        print("Employee Number: ", self.employeeNumber)
        print("Supervisor Name: ", self.supervisorName)
        print("SSN: ", self.SSN)
        print("Company Code: ", self.companyCode)
        print("Company Name: ", self.companyName)
        print("Job Title: ", self.jobTitle)
        print("Status: ", self.status)
        print("Pay Type: ", self.payType)
        print("Hourly Rate: ", self.hourlyPayRate)
        print("Salary Pay Rate: ", self.salaryPayRate)
        print("Pay Frequency: ", self.payFrequency)
        print("flsa Status: ", self.flsaStatus)
        print("Employment Effective Data: ", self.employmentEffectiveDate)
        print("Employment Type: ", self.employmentType)
        print("Email: ", self.emailAddress)
        print("Alt Email: ", self.emailAddressAlt)
        print("Phone #: ", self.phoneNumber)
        print("D.O.B: ", self.dateOfBirth)
        print("Original Hire Date: ", self.originalHireDate)
        print("Last Adjusted Hire Date: ", self.lastAdjustedHireDate)
        print("Scheduled Hours: ", self.scheduledWorkHours)
        print("Terminate Date: ", self.terminationDate)
        print("")
