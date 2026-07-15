import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mirth.connect.connectors.http.HttpDispatcherProperties;
import com.mirth.connect.connectors.tcp.TcpReceiverProperties;
import com.mirth.connect.donkey.model.channel.SourceConnectorProperties;
import com.mirth.connect.model.Channel;
import com.mirth.connect.model.Connector;
import com.mirth.connect.model.Connector.Mode;
import com.mirth.connect.model.Filter;
import com.mirth.connect.model.Transformer;
import com.mirth.connect.model.converters.ObjectXMLSerializer;
import com.mirth.connect.plugins.datatypes.hl7v2.HL7v2DataTypeProperties;
import com.mirth.connect.plugins.datatypes.raw.RawDataTypeProperties;
import com.mirth.connect.plugins.javascriptrule.JavaScriptRule;
import com.mirth.connect.plugins.javascriptstep.JavaScriptStep;

public class BuildChannels {
    private static final String FHIR_URL = "http://10.20.1.207:8090/fhir";

    private static final String ADT_SCRIPT = """
function value(path) { var v = eval(path); return v == null ? '' : v.toString(); }
function id(v) { return v.toLowerCase().replace(/[^a-z0-9\\-.]/g, '-').replace(/-+/g, '-'); }
function date8(v) { return v.length >= 8 ? v.substring(0,4)+'-'+v.substring(4,6)+'-'+v.substring(6,8) : undefined; }
function instant(v) {
    if (v.length < 8) return undefined;
    var t = v.substring(0,4)+'-'+v.substring(4,6)+'-'+v.substring(6,8);
    if (v.length >= 12) t += 'T'+v.substring(8,10)+':'+v.substring(10,12)+':00Z';
    return t;
}
var mrn = value("msg['PID']['PID.3']['PID.3.1']");
if (!mrn) throw 'PID-3.1 MRN is required';
var patientId = 'patient-' + id(mrn);
var encounterNumber = value("msg['PV1']['PV1.19']['PV1.19.1']") || value("msg['MSH']['MSH.10']['MSH.10.1']");
var encounterId = 'encounter-' + id(encounterNumber);
var sex = value("msg['PID']['PID.8']['PID.8.1']");
var gender = sex == 'M' ? 'male' : sex == 'F' ? 'female' : sex == 'O' ? 'other' : 'unknown';
var encounterClass = value("msg['PV1']['PV1.2']['PV1.2.1']");
var classCode = encounterClass == 'I' ? 'IMP' : encounterClass == 'E' ? 'EMER' : 'AMB';
var classDisplay = classCode == 'IMP' ? 'inpatient encounter' : classCode == 'EMER' ? 'emergency' : 'ambulatory';
var patient = {
  resourceType:'Patient', id:patientId,
  identifier:[{system:'https://example.org/mrn',value:mrn}], active:true,
  name:[{family:value("msg['PID']['PID.5']['PID.5.1']"),given:[value("msg['PID']['PID.5']['PID.5.2']")]}],
  gender:gender, birthDate:date8(value("msg['PID']['PID.7']['PID.7.1']"))
};
var encounter = {
  resourceType:'Encounter', id:encounterId, status:'in-progress',
  class:{system:'http://terminology.hl7.org/CodeSystem/v3-ActCode',code:classCode,display:classDisplay},
  subject:{reference:'Patient/'+patientId},
  period:{start:instant(value("msg['PV1']['PV1.44']['PV1.44.1']") || value("msg['MSH']['MSH.7']['MSH.7.1']"))}
};
var trigger = value("msg['MSH']['MSH.9']['MSH.9.2']");
if (trigger == 'A03') encounter.status = 'finished';
var bundle = {resourceType:'Bundle',type:'transaction',entry:[
  {fullUrl:'Patient/'+patientId,resource:patient,request:{method:'PUT',url:'Patient/'+patientId}},
  {fullUrl:'Encounter/'+encounterId,resource:encounter,request:{method:'PUT',url:'Encounter/'+encounterId}}
]};
channelMap.put('fhirPayload', JSON.stringify(bundle));
channelMap.put('messageType', 'ADT^'+trigger);
""";

    private static final String DFT_SCRIPT = """
function value(path) { var v = eval(path); return v == null ? '' : v.toString(); }
function id(v) { return v.toLowerCase().replace(/[^a-z0-9\\-.]/g, '-').replace(/-+/g, '-'); }
function date8(v) { return v.length >= 8 ? v.substring(0,4)+'-'+v.substring(4,6)+'-'+v.substring(6,8) : undefined; }
var mrn = value("msg['PID']['PID.3']['PID.3.1']");
if (!mrn) throw 'PID-3.1 MRN is required';
var patientId = 'patient-' + id(mrn);
var encounterNumber = value("msg['PV1']['PV1.19']['PV1.19.1']") || value("msg['MSH']['MSH.10']['MSH.10.1']");
var encounterId = 'encounter-' + id(encounterNumber);
var claimNumber = value("msg['FT1'][0]['FT1.2']['FT1.2.1']") || value("msg['MSH']['MSH.10']['MSH.10.1']");
var claimId = 'claim-' + id(claimNumber);
var coverageId = 'coverage-' + id(mrn);
var cpt = value("msg['FT1'][0]['FT1.25']['FT1.25.1']") || '99213';
var icd10 = value("msg['FT1'][0]['FT1.19']['FT1.19.1']") || 'I10';
var amountText = value("msg['FT1'][0]['FT1.11']['FT1.11.1']") || '0';
var amount = Number(amountText.replace(/[^0-9.-]/g,''));
if (isNaN(amount)) throw 'FT1-11 transaction amount is invalid';
var payerId = 'payer-demo';
var coverage = {resourceType:'Coverage',id:coverageId,status:'active',beneficiary:{reference:'Patient/'+patientId},payor:[{reference:'Organization/'+payerId}]};
var claim = {
  resourceType:'Claim',id:claimId,identifier:[{system:'https://example.org/claim-id',value:claimNumber}],
  status:'active',type:{coding:[{system:'http://terminology.hl7.org/CodeSystem/claim-type',code:'professional'}]},use:'claim',
  patient:{reference:'Patient/'+patientId},created:date8(value("msg['FT1'][0]['FT1.4']['FT1.4.1']") || value("msg['MSH']['MSH.7']['MSH.7.1']")),
  provider:{reference:'Organization/provider-demo'},priority:{coding:[{system:'http://terminology.hl7.org/CodeSystem/processpriority',code:'normal'}]},
  insurance:[{sequence:1,focal:true,coverage:{reference:'Coverage/'+coverageId}}],
  diagnosis:[{sequence:1,diagnosisCodeableConcept:{coding:[{system:'http://hl7.org/fhir/sid/icd-10-cm',code:icd10}]}}],
  item:[{sequence:1,encounter:[{reference:'Encounter/'+encounterId}],diagnosisSequence:[1],productOrService:{coding:[{system:'http://www.ama-assn.org/go/cpt',code:cpt}]},unitPrice:{value:amount,currency:'USD'}}]
};
var bundle = {resourceType:'Bundle',type:'transaction',entry:[
  {fullUrl:'Coverage/'+coverageId,resource:coverage,request:{method:'PUT',url:'Coverage/'+coverageId}},
  {fullUrl:'Claim/'+claimId,resource:claim,request:{method:'PUT',url:'Claim/'+claimId}}
]};
channelMap.put('fhirPayload', JSON.stringify(bundle));
channelMap.put('messageType', 'DFT^P03');
""";

    private static Transformer transformer(String script) {
        Transformer t = new Transformer();
        t.setInboundTemplate("");
        t.setOutboundTemplate("");
        t.setInboundDataType("HL7V2");
        t.setOutboundDataType("HL7V2");
        t.setInboundProperties(new HL7v2DataTypeProperties());
        t.setOutboundProperties(new HL7v2DataTypeProperties());
        JavaScriptStep step = new JavaScriptStep();
        step.setName("Map HL7 v2 to FHIR R4 transaction");
        step.setSequenceNumber("0");
        step.setEnabled(true);
        step.setScript(script);
        t.setElements(Arrays.asList(step));
        return t;
    }

    private static Transformer rawTransformer() {
        Transformer t = new Transformer();
        t.setInboundTemplate("");
        t.setOutboundTemplate("");
        t.setInboundDataType("RAW");
        t.setOutboundDataType("RAW");
        t.setInboundProperties(new RawDataTypeProperties());
        t.setOutboundProperties(new RawDataTypeProperties());
        return t;
    }

    private static Channel channel(String id, String name, String typePrefix, int port, String script) {
        Channel c = new Channel();
        c.setId(id);
        c.setName(name);
        c.setDescription("Synthetic HL7 v2 " + typePrefix + " to FHIR R4 transaction channel. No PHI.");
        c.setRevision(1);

        TcpReceiverProperties tcp = new TcpReceiverProperties();
        tcp.getListenerConnectorProperties().setPort(Integer.toString(port));
        tcp.getSourceConnectorProperties().setResponseVariable(SourceConnectorProperties.RESPONSE_DESTINATIONS_COMPLETED);
        Connector source = new Connector("HL7 v2 MLLP listener");
        source.setProperties(tcp);
        source.setTransformer(transformer(script));
        JavaScriptRule rule = new JavaScriptRule();
        rule.setName("Require " + typePrefix + " message");
        rule.setSequenceNumber("0");
        rule.setEnabled(true);
        rule.setScript("return msg['MSH']['MSH.9']['MSH.9.1'].toString() == '" + typePrefix + "';");
        Filter filter = new Filter();
        filter.setElements(Arrays.asList(rule));
        source.setFilter(filter);
        source.setTransportName("TCP Listener");
        source.setMode(Mode.SOURCE);
        source.setEnabled(true);
        c.setSourceConnector(source);

        HttpDispatcherProperties http = new HttpDispatcherProperties();
        http.setHost(FHIR_URL);
        http.setMethod("post");
        http.setContent("${fhirPayload}");
        http.setContentType("application/fhir+json");
        Map<String, List<String>> headers = new LinkedHashMap<>();
        headers.put("Accept", Arrays.asList("application/fhir+json"));
        http.setHeadersMap(headers);
        http.getDestinationConnectorProperties().setRetryCount(3);
        http.getDestinationConnectorProperties().setRetryIntervalMillis(5000);
        Connector destination = new Connector("HAPI FHIR transaction");
        destination.setProperties(http);
        destination.setTransformer(rawTransformer());
        destination.setResponseTransformer(rawTransformer());
        destination.setFilter(new Filter());
        destination.setTransportName("HTTP Sender");
        destination.setMode(Mode.DESTINATION);
        destination.setEnabled(true);
        c.addDestination(destination);

        c.setPreprocessingScript("return message;");
        c.setPostprocessingScript("return;");
        c.setDeployScript("return;");
        c.setUndeployScript("return;");
        c.getProperties().setStoreAttachments(false);
        return c;
    }

    public static void main(String[] args) throws Exception {
        ObjectXMLSerializer serializer = ObjectXMLSerializer.getInstance();
        serializer.init("4.5.2");
        Path out = Path.of(args.length == 0 ? "." : args[0]);
        Files.createDirectories(out);
        Channel adt = channel("de82d30f-9f6e-4c03-ae21-0788cbdc6661", "RCM ADT to FHIR", "ADT", 6661, ADT_SCRIPT);
        Channel dft = channel("5ac2b9aa-b231-4bb3-8f43-e5959e1d6662", "RCM DFT to FHIR Claim", "DFT", 6662, DFT_SCRIPT);
        Files.writeString(out.resolve("adt-to-fhir.xml"), serializer.serialize(adt));
        Files.writeString(out.resolve("dft-to-fhir.xml"), serializer.serialize(dft));
    }
}
