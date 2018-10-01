/run for i=1,GetNumGroupMembers() do local u="party"..i print(format("%s-%s", GetUnitName(u),GetRealmName(u))) end
/run local n,r=UnitFullName("party1") if n then SendChatMessage(format("%s-%s",n,GetRealmName()),"party") end
/run local n,r=UnitFullName("party1") if n then SendChatMessage(format("%s-%s",n,GetRealmName()),"party") end
