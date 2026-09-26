// Private analysis export. Automatically inferred code is not verified semantics.
// @category RacingBois.Research
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import com.google.gson.GsonBuilder;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class ExportReference extends GhidraScript {
    @Override public void run() throws Exception {
        String[] args=getScriptArgs();
        if(args.length!=1)throw new IllegalArgumentException("Supply private output directory");
        Path out=Paths.get(args[0]).toAbsolutePath();
        if(!out.toString().contains("ReferenceOnly"))throw new IllegalArgumentException("Private output required");
        Files.createDirectories(out.resolve("functions"));
        Map<Long,String> names=new LinkedHashMap<>();
        names.put(0x405e30L,"rb_load_specs");names.put(0x405ea0L,"rb_initialize_specs_cached");
        names.put(0x42efc0L,"rb_save_checksum");names.put(0x42f000L,"rb_write_save");
        names.put(0x42f110L,"rb_read_save");names.put(0x4436a0L,"rb_load_dat_bank");
        for(Map.Entry<Long,String> entry:names.entrySet()){
            Function f=currentProgram.getFunctionManager().getFunctionAt(toAddr(entry.getKey()));
            if(f!=null)f.setName(entry.getValue(),SourceType.USER_DEFINED);
        }
        DecompInterface d=new DecompInterface();d.toggleCCode(true);d.toggleSyntaxTree(false);
        d.setSimplificationStyle("decompile");
        if(!d.openProgram(currentProgram))throw new IllegalStateException(d.getLastMessage());
        List<Map<String,Object>> functions=new ArrayList<>();int success=0,failed=0;
        FunctionIterator iterator=currentProgram.getFunctionManager().getFunctions(true);
        try {
            while(iterator.hasNext()&&!monitor.isCancelled()){
                Function f=iterator.next();if(f.isExternal())continue;
                Map<String,Object> record=new LinkedHashMap<>();String address=f.getEntryPoint().toString();
                record.put("address",address);record.put("name",f.getName());
                record.put("body_address_count",f.getBody().getNumAddresses());
                record.put("signature_inferred",f.getSignature().toString());
                Set<String> calls=new TreeSet<>();for(Function c:f.getCalledFunctions(monitor))calls.add(c.getEntryPoint()+":"+c.getName());
                record.put("callees",calls);List<Map<String,Object>> refs=new ArrayList<>();
                InstructionIterator instructions=currentProgram.getListing().getInstructions(f.getBody(),true);int count=0;
                while(instructions.hasNext()){
                    Instruction ins=instructions.next();count++;
                    for(Reference ref:ins.getReferencesFrom()){
                        if(ref.getReferenceType().isFlow())continue;
                        Map<String,Object> item=new LinkedHashMap<>();item.put("from",ins.getAddress().toString());
                        item.put("to",ref.getToAddress().toString());item.put("type",ref.getReferenceType().toString());
                        Data data=currentProgram.getListing().getDataAt(ref.getToAddress());
                        if(data!=null&&data.hasStringValue())item.put("string",String.valueOf(data.getValue()));refs.add(item);
                    }
                }
                record.put("instructions",count);record.put("data_references",refs);
                DecompileResults result=d.decompileFunction(f,20,monitor);
                boolean ok=result.decompileCompleted()&&result.getDecompiledFunction()!=null;
                record.put("decompiled",ok);record.put("error",result.getErrorMessage());
                if(ok){Files.writeString(out.resolve("functions").resolve(address+".c"),result.getDecompiledFunction().getC(),StandardCharsets.UTF_8);success++;}
                else failed++;functions.add(record);
            }
        } finally {d.dispose();}
        Map<String,Object> report=new LinkedHashMap<>();report.put("program",currentProgram.getName());
        report.put("generated_utc",java.time.Instant.now().toString());report.put("functions_discovered",functions.size());
        report.put("decompiled",success);report.put("failed",failed);report.put("cancelled",monitor.isCancelled());
        report.put("scope","Automatic navigation only; calling conventions, types, branches and gameplay semantics require review.");report.put("functions",functions);
        Files.writeString(out.resolve("function_catalog.json"),new GsonBuilder().setPrettyPrinting().create().toJson(report),StandardCharsets.UTF_8);
        println("RB_EXPORT_DONE functions="+functions.size()+" decompiled="+success+" failed="+failed);
    }
}
