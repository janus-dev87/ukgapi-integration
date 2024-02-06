class Earnings(object):
    def __init__(self):
        self.recordType = "S2"
        self.employeeNumber = ""
        self.companyCode = ""
        self.SSN = ""
        self.earningCode = ""
        self.payDate = ""
        self.baseAmout = 0.0

    def employeeNumberCompanyCode(self):
        return self.employeeNumber + self.companyCode

    def print(self):
        print("Employee Number: ", self.employeeNumber)
        print("Company Code: ", self.companyCode)
        print("SSN: ", self.SSN)
        print("Earnings Code: ", self.earningCode)
        print("Pay Date: ", self.payDate)
        print("Base Amount: ", self.baseAmout)
        print("")


