# Mirth Connect integration lab

This deployment runs on the dedicated `hl7-mirth-lab` LXC. It accepts only
synthetic data and forwards mapped FHIR R4 resources to the HAPI FHIR server.

- Administrator: `https://10.20.1.157:8443`
- ADT MLLP listener: `10.20.1.157:6661`
- DFT MLLP listener: `10.20.1.157:6662`
- FHIR destination: `http://10.20.1.207:8090/fhir`

Copy `.env.example` to `.env`, generate a unique database password, and run
`docker-compose up -d`. Never use real patient data in this lab.
