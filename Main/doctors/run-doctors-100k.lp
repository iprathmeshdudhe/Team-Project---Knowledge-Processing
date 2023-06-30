prescription(Id, Patient, Npi, c1) :- treatment(Id, Patient, Hospital, Npi, Conf1), physician(Npi, Name, Spec, Conf2).
doctor(Npi, Doctor, Spec, h, c2) :- medprescription(Id, Patient, Npi, Doctor, Spec, Conf).
prescription(Id, Patient, Npi, c1) :- medprescription(Id, Patient, Npi, Doctor, Spec, Conf).
doctor(Npi, Name, Spec, Hospital, c2) :- treatment(Id, Patient, Hospital, Npi, Conf1), physician(Npi, Name, Spec, Conf2).
targethospital(Doctor, Spec, Hospital1, Npi1, Hconf1) :- hospital(Doctor, Spec, Hospital1, Npi1, Hconf1).