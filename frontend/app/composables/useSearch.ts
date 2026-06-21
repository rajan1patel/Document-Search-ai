import {api} from "~/utils/api"



export function useSearch(){



async function search(
query:string,
limit:number=5
){


const response =
await api.post(
"/search",
{
query,
limit
}
)


return response.data

}



return {

search

}

}