import {api} from "~/utils/api"



export function useDocuments(){


async function getDocuments(){


const res =
await api.get(
"/documents"
)


return res.data

}




async function uploadDocument(
file:File
){


const form =
new FormData()


form.append(
"file",
file
)


return api.post(
"/documents/upload",
form
)

}



async function removeDocument(
id:number
){

return api.delete(
`/documents/${id}`
)

}



return {

getDocuments,

uploadDocument,

removeDocument

}


}