import { emptySplitApi as api } from "./emptyApi";
const injectedRtkApi = api.injectEndpoints({
  endpoints: (build) => ({
    getUsers: build.query<GetUsersApiResponse, GetUsersApiArg>({
      query: () => ({ url: `/v1/user` }),
    }),
  }),
  overrideExisting: false,
});
export { injectedRtkApi as serverApi };
export type GetUsersApiResponse = /** status 200 UserSchema */ UserSchema[];
export type GetUsersApiArg = void;
export type UserSchema = {
  active?: boolean | null;
  confirmed_at?: string | null;
  date_created?: string | null;
  date_modified?: string | null;
  email?: string | null;
  first_name?: string | null;
  id?: number;
  last_name?: string | null;
  password?: string | null;
  proof?: string | null;
};
export type Error = {
  errors?: object;
  message: string;
};
export const { useGetUsersQuery } = injectedRtkApi;
