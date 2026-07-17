# Generated from /Users/eunsang/Documents/Sources/metchurial-antlr/vendor/grammars-v4/Db2Parser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .Db2Parser import Db2Parser
else:
    from Db2Parser import Db2Parser

# This class defines a complete generic visitor for a parse tree produced by Db2Parser.

class Db2ParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by Db2Parser#db2_file.
    def visitDb2_file(self, ctx:Db2Parser.Db2_fileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#batch.
    def visitBatch(self, ctx:Db2Parser.BatchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_statement.
    def visitSql_statement(self, ctx:Db2Parser.Sql_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_schema_statement.
    def visitSql_schema_statement(self, ctx:Db2Parser.Sql_schema_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_data_change_statement.
    def visitSql_data_change_statement(self, ctx:Db2Parser.Sql_data_change_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_data_statement.
    def visitSql_data_statement(self, ctx:Db2Parser.Sql_data_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_transaction_statement.
    def visitSql_transaction_statement(self, ctx:Db2Parser.Sql_transaction_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_connection_statement.
    def visitSql_connection_statement(self, ctx:Db2Parser.Sql_connection_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_dynamic_statement.
    def visitSql_dynamic_statement(self, ctx:Db2Parser.Sql_dynamic_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_session_statement.
    def visitSql_session_statement(self, ctx:Db2Parser.Sql_session_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_embedded_host_language_statement.
    def visitSql_embedded_host_language_statement(self, ctx:Db2Parser.Sql_embedded_host_language_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_constrol_statement.
    def visitSql_constrol_statement(self, ctx:Db2Parser.Sql_constrol_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#select_statement.
    def visitSelect_statement(self, ctx:Db2Parser.Select_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#read_only_clause.
    def visitRead_only_clause(self, ctx:Db2Parser.Read_only_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#update_clause.
    def visitUpdate_clause(self, ctx:Db2Parser.Update_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#optimize_for_clause.
    def visitOptimize_for_clause(self, ctx:Db2Parser.Optimize_for_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#concurrent_access_resolution_clause.
    def visitConcurrent_access_resolution_clause(self, ctx:Db2Parser.Concurrent_access_resolution_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#delete_statement.
    def visitDelete_statement(self, ctx:Db2Parser.Delete_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#delete_statement_searched_delete.
    def visitDelete_statement_searched_delete(self, ctx:Db2Parser.Delete_statement_searched_deleteContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_or_view_name.
    def visitTable_or_view_name(self, ctx:Db2Parser.Table_or_view_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#delete_statement_positioned_delete.
    def visitDelete_statement_positioned_delete(self, ctx:Db2Parser.Delete_statement_positioned_deleteContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#delete_deltalake_statement.
    def visitDelete_deltalake_statement(self, ctx:Db2Parser.Delete_deltalake_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#insert_statement.
    def visitInsert_statement(self, ctx:Db2Parser.Insert_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#insert_datalake_statement.
    def visitInsert_datalake_statement(self, ctx:Db2Parser.Insert_datalake_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#values_item.
    def visitValues_item(self, ctx:Db2Parser.Values_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#merge_statement.
    def visitMerge_statement(self, ctx:Db2Parser.Merge_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_view_fullselect.
    def visitTable_view_fullselect(self, ctx:Db2Parser.Table_view_fullselectContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#common_table_expression_list.
    def visitCommon_table_expression_list(self, ctx:Db2Parser.Common_table_expression_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#matching_condition.
    def visitMatching_condition(self, ctx:Db2Parser.Matching_conditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#modification_operation.
    def visitModification_operation(self, ctx:Db2Parser.Modification_operationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#update_operation.
    def visitUpdate_operation(self, ctx:Db2Parser.Update_operationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#delete_operation.
    def visitDelete_operation(self, ctx:Db2Parser.Delete_operationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#insert_operation.
    def visitInsert_operation(self, ctx:Db2Parser.Insert_operationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#expr_null_default_list.
    def visitExpr_null_default_list(self, ctx:Db2Parser.Expr_null_default_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#isolation_level.
    def visitIsolation_level(self, ctx:Db2Parser.Isolation_levelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#truncate_statement.
    def visitTruncate_statement(self, ctx:Db2Parser.Truncate_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#update_statement.
    def visitUpdate_statement(self, ctx:Db2Parser.Update_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#update_statement_searched_update.
    def visitUpdate_statement_searched_update(self, ctx:Db2Parser.Update_statement_searched_updateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#skip_wait.
    def visitSkip_wait(self, ctx:Db2Parser.Skip_waitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#update_statement_positioned_update.
    def visitUpdate_statement_positioned_update(self, ctx:Db2Parser.Update_statement_positioned_updateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#include_columns.
    def visitInclude_columns(self, ctx:Db2Parser.Include_columnsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#assignment_clause.
    def visitAssignment_clause(self, ctx:Db2Parser.Assignment_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#assignment_item.
    def visitAssignment_item(self, ctx:Db2Parser.Assignment_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#period_clause.
    def visitPeriod_clause(self, ctx:Db2Parser.Period_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#time_sec.
    def visitTime_sec(self, ctx:Db2Parser.Time_secContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#update_datalake_statement.
    def visitUpdate_datalake_statement(self, ctx:Db2Parser.Update_datalake_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_database_authorities_statement.
    def visitGrant_database_authorities_statement(self, ctx:Db2Parser.Grant_database_authorities_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_privilege_list.
    def visitDb_privilege_list(self, ctx:Db2Parser.Db_privilege_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_privilege.
    def visitDb_privilege(self, ctx:Db2Parser.Db_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grantee.
    def visitGrantee(self, ctx:Db2Parser.GranteeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grantee_user_group.
    def visitGrantee_user_group(self, ctx:Db2Parser.Grantee_user_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#user_group.
    def visitUser_group(self, ctx:Db2Parser.User_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grantee_list.
    def visitGrantee_list(self, ctx:Db2Parser.Grantee_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grantee_list_public.
    def visitGrantee_list_public(self, ctx:Db2Parser.Grantee_list_publicContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grantee_list_user_group.
    def visitGrantee_list_user_group(self, ctx:Db2Parser.Grantee_list_user_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_exemption_statement.
    def visitGrant_exemption_statement(self, ctx:Db2Parser.Grant_exemption_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#exemption_privilege.
    def visitExemption_privilege(self, ctx:Db2Parser.Exemption_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_global_variable_privileges_statement.
    def visitGrant_global_variable_privileges_statement(self, ctx:Db2Parser.Grant_global_variable_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#variable_privilege.
    def visitVariable_privilege(self, ctx:Db2Parser.Variable_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#read_write.
    def visitRead_write(self, ctx:Db2Parser.Read_writeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#with_grant_option.
    def visitWith_grant_option(self, ctx:Db2Parser.With_grant_optionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_index_privileges_statement.
    def visitGrant_index_privileges_statement(self, ctx:Db2Parser.Grant_index_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_module_privileges_statement.
    def visitGrant_module_privileges_statement(self, ctx:Db2Parser.Grant_module_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_package_privileges_statement.
    def visitGrant_package_privileges_statement(self, ctx:Db2Parser.Grant_package_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#package_privilege_list.
    def visitPackage_privilege_list(self, ctx:Db2Parser.Package_privilege_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#package_privilege.
    def visitPackage_privilege(self, ctx:Db2Parser.Package_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_role_statement.
    def visitGrant_role_statement(self, ctx:Db2Parser.Grant_role_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#role_list.
    def visitRole_list(self, ctx:Db2Parser.Role_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_routine_privileges_statement.
    def visitGrant_routine_privileges_statement(self, ctx:Db2Parser.Grant_routine_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_schema_privileges_statement.
    def visitGrant_schema_privileges_statement(self, ctx:Db2Parser.Grant_schema_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#schema_privilege_list.
    def visitSchema_privilege_list(self, ctx:Db2Parser.Schema_privilege_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#schema_privilege.
    def visitSchema_privilege(self, ctx:Db2Parser.Schema_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_security_label_statement.
    def visitGrant_security_label_statement(self, ctx:Db2Parser.Grant_security_label_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_sequence_privileges_statement.
    def visitGrant_sequence_privileges_statement(self, ctx:Db2Parser.Grant_sequence_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sequence_privilege_list.
    def visitSequence_privilege_list(self, ctx:Db2Parser.Sequence_privilege_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sequence_privilege.
    def visitSequence_privilege(self, ctx:Db2Parser.Sequence_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_server_privileges_statement.
    def visitGrant_server_privileges_statement(self, ctx:Db2Parser.Grant_server_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_setsessionuser_privilege_statement.
    def visitGrant_setsessionuser_privilege_statement(self, ctx:Db2Parser.Grant_setsessionuser_privilege_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#user_list.
    def visitUser_list(self, ctx:Db2Parser.User_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#user_auth.
    def visitUser_auth(self, ctx:Db2Parser.User_authContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_table_space_privileges_statement.
    def visitGrant_table_space_privileges_statement(self, ctx:Db2Parser.Grant_table_space_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_table_view_or_nickname_privileges_statement.
    def visitGrant_table_view_or_nickname_privileges_statement(self, ctx:Db2Parser.Grant_table_view_or_nickname_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tvn_privilege_list.
    def visitTvn_privilege_list(self, ctx:Db2Parser.Tvn_privilege_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tvn_privilege.
    def visitTvn_privilege(self, ctx:Db2Parser.Tvn_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_name_list_paren.
    def visitColumn_name_list_paren(self, ctx:Db2Parser.Column_name_list_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_name_list.
    def visitColumn_name_list(self, ctx:Db2Parser.Column_name_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_workload_privileges_statement.
    def visitGrant_workload_privileges_statement(self, ctx:Db2Parser.Grant_workload_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_xsr_object_privileges_statement.
    def visitGrant_xsr_object_privileges_statement(self, ctx:Db2Parser.Grant_xsr_object_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_database_authorities_statement.
    def visitRevoke_database_authorities_statement(self, ctx:Db2Parser.Revoke_database_authorities_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#by_all.
    def visitBy_all(self, ctx:Db2Parser.By_allContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_exemption_statement.
    def visitRevoke_exemption_statement(self, ctx:Db2Parser.Revoke_exemption_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_global_variable_privileges_statement.
    def visitRevoke_global_variable_privileges_statement(self, ctx:Db2Parser.Revoke_global_variable_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_index_privileges_statement.
    def visitRevoke_index_privileges_statement(self, ctx:Db2Parser.Revoke_index_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_module_privileges_statement.
    def visitRevoke_module_privileges_statement(self, ctx:Db2Parser.Revoke_module_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_package_privileges_statement.
    def visitRevoke_package_privileges_statement(self, ctx:Db2Parser.Revoke_package_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_role_statement.
    def visitRevoke_role_statement(self, ctx:Db2Parser.Revoke_role_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_routine_privileges_statement.
    def visitRevoke_routine_privileges_statement(self, ctx:Db2Parser.Revoke_routine_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_schema_privileges_statement.
    def visitRevoke_schema_privileges_statement(self, ctx:Db2Parser.Revoke_schema_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_security_label_statement.
    def visitRevoke_security_label_statement(self, ctx:Db2Parser.Revoke_security_label_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_sequence_privileges_statement.
    def visitRevoke_sequence_privileges_statement(self, ctx:Db2Parser.Revoke_sequence_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_server_privileges_statement.
    def visitRevoke_server_privileges_statement(self, ctx:Db2Parser.Revoke_server_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_setsessionuser_privilege_statement.
    def visitRevoke_setsessionuser_privilege_statement(self, ctx:Db2Parser.Revoke_setsessionuser_privilege_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_table_space_privileges_statement.
    def visitRevoke_table_space_privileges_statement(self, ctx:Db2Parser.Revoke_table_space_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_table_view_or_nickname_privileges_statement.
    def visitRevoke_table_view_or_nickname_privileges_statement(self, ctx:Db2Parser.Revoke_table_view_or_nickname_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_workload_privileges_statement.
    def visitRevoke_workload_privileges_statement(self, ctx:Db2Parser.Revoke_workload_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#revoke_xsr_object_privileges_statement.
    def visitRevoke_xsr_object_privileges_statement(self, ctx:Db2Parser.Revoke_xsr_object_privileges_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#user_group_role.
    def visitUser_group_role(self, ctx:Db2Parser.User_group_roleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#rollback_statement.
    def visitRollback_statement(self, ctx:Db2Parser.Rollback_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#savepoint_statement.
    def visitSavepoint_statement(self, ctx:Db2Parser.Savepoint_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#release_savepoint_statement.
    def visitRelease_savepoint_statement(self, ctx:Db2Parser.Release_savepoint_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#allocate_cursor_statement.
    def visitAllocate_cursor_statement(self, ctx:Db2Parser.Allocate_cursor_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_audit_policy_statement.
    def visitAlter_audit_policy_statement(self, ctx:Db2Parser.Alter_audit_policy_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#status_spec.
    def visitStatus_spec(self, ctx:Db2Parser.Status_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#normal_audit.
    def visitNormal_audit(self, ctx:Db2Parser.Normal_auditContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_bufferpool_statement.
    def visitAlter_bufferpool_statement(self, ctx:Db2Parser.Alter_bufferpool_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#immediate_deferred.
    def visitImmediate_deferred(self, ctx:Db2Parser.Immediate_deferredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_database_partition_group_statement.
    def visitAlter_database_partition_group_statement(self, ctx:Db2Parser.Alter_database_partition_group_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_partition_group_list_item.
    def visitDb_partition_group_list_item(self, ctx:Db2Parser.Db_partition_group_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_partition_num_nums.
    def visitDb_partition_num_nums(self, ctx:Db2Parser.Db_partition_num_numsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_partitions_clause.
    def visitDb_partitions_clause(self, ctx:Db2Parser.Db_partitions_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_partition_options.
    def visitDb_partition_options(self, ctx:Db2Parser.Db_partition_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_database_statement.
    def visitAlter_database_statement(self, ctx:Db2Parser.Alter_database_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_database_opts.
    def visitAlter_database_opts(self, ctx:Db2Parser.Alter_database_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_event_monitor_statement.
    def visitAlter_event_monitor_statement(self, ctx:Db2Parser.Alter_event_monitor_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_event_monitor_opts.
    def visitAlter_event_monitor_opts(self, ctx:Db2Parser.Alter_event_monitor_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_function_statement.
    def visitAlter_function_statement(self, ctx:Db2Parser.Alter_function_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_function_opts.
    def visitAlter_function_opts(self, ctx:Db2Parser.Alter_function_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#function_designator.
    def visitFunction_designator(self, ctx:Db2Parser.Function_designatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_type_list.
    def visitData_type_list(self, ctx:Db2Parser.Data_type_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_type_list_paren.
    def visitData_type_list_paren(self, ctx:Db2Parser.Data_type_list_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_histogram_template_statement.
    def visitAlter_histogram_template_statement(self, ctx:Db2Parser.Alter_histogram_template_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_index_statement.
    def visitAlter_index_statement(self, ctx:Db2Parser.Alter_index_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#yes_no.
    def visitYes_no(self, ctx:Db2Parser.Yes_noContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_mask_statement.
    def visitAlter_mask_statement(self, ctx:Db2Parser.Alter_mask_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#enable_disable.
    def visitEnable_disable(self, ctx:Db2Parser.Enable_disableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_method_statement.
    def visitAlter_method_statement(self, ctx:Db2Parser.Alter_method_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_designator.
    def visitMethod_designator(self, ctx:Db2Parser.Method_designatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_model_statement.
    def visitAlter_model_statement(self, ctx:Db2Parser.Alter_model_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_module_statement.
    def visitAlter_module_statement(self, ctx:Db2Parser.Alter_module_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_module_opts.
    def visitAlter_module_opts(self, ctx:Db2Parser.Alter_module_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_function_definition.
    def visitModule_function_definition(self, ctx:Db2Parser.Module_function_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_procedure_definition.
    def visitModule_procedure_definition(self, ctx:Db2Parser.Module_procedure_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_type_definition.
    def visitModule_type_definition(self, ctx:Db2Parser.Module_type_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_variable_definition.
    def visitModule_variable_definition(self, ctx:Db2Parser.Module_variable_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_condition_definition.
    def visitModule_condition_definition(self, ctx:Db2Parser.Module_condition_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_object_identification.
    def visitModule_object_identification(self, ctx:Db2Parser.Module_object_identificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_function_designator.
    def visitModule_function_designator(self, ctx:Db2Parser.Module_function_designatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_procedure_designator.
    def visitModule_procedure_designator(self, ctx:Db2Parser.Module_procedure_designatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_nickname_statement.
    def visitAlter_nickname_statement(self, ctx:Db2Parser.Alter_nickname_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_nickname_opts_1.
    def visitAlter_nickname_opts_1(self, ctx:Db2Parser.Alter_nickname_opts_1Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_nickname_opts_1_item.
    def visitAlter_nickname_opts_1_item(self, ctx:Db2Parser.Alter_nickname_opts_1_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_nickname_opts_2.
    def visitAlter_nickname_opts_2(self, ctx:Db2Parser.Alter_nickname_opts_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_nickname_opts_2_item.
    def visitAlter_nickname_opts_2_item(self, ctx:Db2Parser.Alter_nickname_opts_2_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#constraint_alteration.
    def visitConstraint_alteration(self, ctx:Db2Parser.Constraint_alterationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_package_statement.
    def visitAlter_package_statement(self, ctx:Db2Parser.Alter_package_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_package_opts.
    def visitAlter_package_opts(self, ctx:Db2Parser.Alter_package_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_permission_statement.
    def visitAlter_permission_statement(self, ctx:Db2Parser.Alter_permission_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_procedure_external_statement.
    def visitAlter_procedure_external_statement(self, ctx:Db2Parser.Alter_procedure_external_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_procedure_external_opts.
    def visitAlter_procedure_external_opts(self, ctx:Db2Parser.Alter_procedure_external_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#procedure_designator.
    def visitProcedure_designator(self, ctx:Db2Parser.Procedure_designatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_procedure_sourced_statement.
    def visitAlter_procedure_sourced_statement(self, ctx:Db2Parser.Alter_procedure_sourced_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#parameter_alteration.
    def visitParameter_alteration(self, ctx:Db2Parser.Parameter_alterationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_procedure_sql_statement.
    def visitAlter_procedure_sql_statement(self, ctx:Db2Parser.Alter_procedure_sql_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_schema_statement.
    def visitAlter_schema_statement(self, ctx:Db2Parser.Alter_schema_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#none_changes.
    def visitNone_changes(self, ctx:Db2Parser.None_changesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_security_label_component_statement.
    def visitAlter_security_label_component_statement(self, ctx:Db2Parser.Alter_security_label_component_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#add_element_clause.
    def visitAdd_element_clause(self, ctx:Db2Parser.Add_element_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#array_element_clause.
    def visitArray_element_clause(self, ctx:Db2Parser.Array_element_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tree_element_clause.
    def visitTree_element_clause(self, ctx:Db2Parser.Tree_element_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_security_policy_statement.
    def visitAlter_security_policy_statement(self, ctx:Db2Parser.Alter_security_policy_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_security_policy_opts.
    def visitAlter_security_policy_opts(self, ctx:Db2Parser.Alter_security_policy_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_sequence_statement.
    def visitAlter_sequence_statement(self, ctx:Db2Parser.Alter_sequence_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_sequence_opts.
    def visitAlter_sequence_opts(self, ctx:Db2Parser.Alter_sequence_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_server_statement.
    def visitAlter_server_statement(self, ctx:Db2Parser.Alter_server_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_server_opts.
    def visitAlter_server_opts(self, ctx:Db2Parser.Alter_server_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_service_class_statement.
    def visitAlter_service_class_statement(self, ctx:Db2Parser.Alter_service_class_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_service_class_opts.
    def visitAlter_service_class_opts(self, ctx:Db2Parser.Alter_service_class_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#default_on_off.
    def visitDefault_on_off(self, ctx:Db2Parser.Default_on_offContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#default_high_medium_low.
    def visitDefault_high_medium_low(self, ctx:Db2Parser.Default_high_medium_lowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_stogroup_statement.
    def visitAlter_stogroup_statement(self, ctx:Db2Parser.Alter_stogroup_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_stogroup_opts.
    def visitAlter_stogroup_opts(self, ctx:Db2Parser.Alter_stogroup_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_table_statement.
    def visitAlter_table_statement(self, ctx:Db2Parser.Alter_table_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_table_opts.
    def visitAlter_table_opts(self, ctx:Db2Parser.Alter_table_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#null_on_off.
    def visitNull_on_off(self, ctx:Db2Parser.Null_on_offContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#cascade_restrict.
    def visitCascade_restrict(self, ctx:Db2Parser.Cascade_restrictContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#materialized_query_definition.
    def visitMaterialized_query_definition(self, ctx:Db2Parser.Materialized_query_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#refreshable_table_options.
    def visitRefreshable_table_options(self, ctx:Db2Parser.Refreshable_table_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_alteration.
    def visitColumn_alteration(self, ctx:Db2Parser.Column_alterationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#generation_alteration.
    def visitGeneration_alteration(self, ctx:Db2Parser.Generation_alterationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#identity_alteration.
    def visitIdentity_alteration(self, ctx:Db2Parser.Identity_alterationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#generation_attribute.
    def visitGeneration_attribute(self, ctx:Db2Parser.Generation_attributeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#as_identity_clause.
    def visitAs_identity_clause(self, ctx:Db2Parser.As_identity_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#as_identity_clause_opts.
    def visitAs_identity_clause_opts(self, ctx:Db2Parser.As_identity_clause_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#period_definition_alter.
    def visitPeriod_definition_alter(self, ctx:Db2Parser.Period_definition_alterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#add_partition.
    def visitAdd_partition(self, ctx:Db2Parser.Add_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#boundary_spec_alter.
    def visitBoundary_spec_alter(self, ctx:Db2Parser.Boundary_spec_alterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#attach_partition.
    def visitAttach_partition(self, ctx:Db2Parser.Attach_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#activate_deactivate.
    def visitActivate_deactivate(self, ctx:Db2Parser.Activate_deactivateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_tablespace_statement.
    def visitAlter_tablespace_statement(self, ctx:Db2Parser.Alter_tablespace_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_tablespace_opts.
    def visitAlter_tablespace_opts(self, ctx:Db2Parser.Alter_tablespace_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#add_clause.
    def visitAdd_clause(self, ctx:Db2Parser.Add_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_container_clause.
    def visitDb_container_clause(self, ctx:Db2Parser.Db_container_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_container_clause_opts.
    def visitDb_container_clause_opts(self, ctx:Db2Parser.Db_container_clause_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#drop_container_clause.
    def visitDrop_container_clause(self, ctx:Db2Parser.Drop_container_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#file_device.
    def visitFile_device(self, ctx:Db2Parser.File_deviceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#all_containers_clause.
    def visitAll_containers_clause(self, ctx:Db2Parser.All_containers_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#system_container_clause.
    def visitSystem_container_clause(self, ctx:Db2Parser.System_container_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#stripeset.
    def visitStripeset(self, ctx:Db2Parser.StripesetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#km.
    def visitKm(self, ctx:Db2Parser.KmContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#kmg_percent.
    def visitKmg_percent(self, ctx:Db2Parser.Kmg_percentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_threshold_statement.
    def visitAlter_threshold_statement(self, ctx:Db2Parser.Alter_threshold_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_threshold_opts.
    def visitAlter_threshold_opts(self, ctx:Db2Parser.Alter_threshold_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_threshold_predicate.
    def visitAlter_threshold_predicate(self, ctx:Db2Parser.Alter_threshold_predicateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_threshold_exceeded_actions.
    def visitAlter_threshold_exceeded_actions(self, ctx:Db2Parser.Alter_threshold_exceeded_actionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#dt_units.
    def visitDt_units(self, ctx:Db2Parser.Dt_unitsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#dt_units_with_seconds.
    def visitDt_units_with_seconds(self, ctx:Db2Parser.Dt_units_with_secondsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_trigger_statement.
    def visitAlter_trigger_statement(self, ctx:Db2Parser.Alter_trigger_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_trusted_context_statement.
    def visitAlter_trusted_context_statement(self, ctx:Db2Parser.Alter_trusted_context_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_trusted_context_opts.
    def visitAlter_trusted_context_opts(self, ctx:Db2Parser.Alter_trusted_context_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_trusted_context_opts_alter_opts.
    def visitAlter_trusted_context_opts_alter_opts(self, ctx:Db2Parser.Alter_trusted_context_opts_alter_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#addr_clause_encryption_val.
    def visitAddr_clause_encryption_val(self, ctx:Db2Parser.Addr_clause_encryption_valContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#address_clause.
    def visitAddress_clause(self, ctx:Db2Parser.Address_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#user_clause.
    def visitUser_clause(self, ctx:Db2Parser.User_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#use_for_opts.
    def visitUse_for_opts(self, ctx:Db2Parser.Use_for_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#use_for_opts_2.
    def visitUse_for_opts_2(self, ctx:Db2Parser.Use_for_opts_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_type_statement.
    def visitAlter_type_statement(self, ctx:Db2Parser.Alter_type_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_type_opts.
    def visitAlter_type_opts(self, ctx:Db2Parser.Alter_type_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_identifier.
    def visitMethod_identifier(self, ctx:Db2Parser.Method_identifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_options.
    def visitMethod_options(self, ctx:Db2Parser.Method_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_usage_list_statement.
    def visitAlter_usage_list_statement(self, ctx:Db2Parser.Alter_usage_list_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_usage_list_opts_item.
    def visitAlter_usage_list_opts_item(self, ctx:Db2Parser.Alter_usage_list_opts_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_user_mapping_statement.
    def visitAlter_user_mapping_statement(self, ctx:Db2Parser.Alter_user_mapping_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_user_mapping_opts_item.
    def visitAlter_user_mapping_opts_item(self, ctx:Db2Parser.Alter_user_mapping_opts_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#add_set.
    def visitAdd_set(self, ctx:Db2Parser.Add_setContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_view_statement.
    def visitAlter_view_statement(self, ctx:Db2Parser.Alter_view_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_view_opts.
    def visitAlter_view_opts(self, ctx:Db2Parser.Alter_view_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_work_action_set_statement.
    def visitAlter_work_action_set_statement(self, ctx:Db2Parser.Alter_work_action_set_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_work_action_set_opts.
    def visitAlter_work_action_set_opts(self, ctx:Db2Parser.Alter_work_action_set_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_action_alteration.
    def visitWork_action_alteration(self, ctx:Db2Parser.Work_action_alterationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_action_alteration_opts.
    def visitWork_action_alteration_opts(self, ctx:Db2Parser.Work_action_alteration_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_action_types_clause.
    def visitAlter_action_types_clause(self, ctx:Db2Parser.Alter_action_types_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#threshold_predicate_clause.
    def visitThreshold_predicate_clause(self, ctx:Db2Parser.Threshold_predicate_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_work_class_set_statement.
    def visitAlter_work_class_set_statement(self, ctx:Db2Parser.Alter_work_class_set_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_work_class_set_opts.
    def visitAlter_work_class_set_opts(self, ctx:Db2Parser.Alter_work_class_set_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_class_alteration.
    def visitWork_class_alteration(self, ctx:Db2Parser.Work_class_alterationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_class_alteration_opts.
    def visitWork_class_alteration_opts(self, ctx:Db2Parser.Work_class_alteration_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#for_from_to_alter_clause.
    def visitFor_from_to_alter_clause(self, ctx:Db2Parser.For_from_to_alter_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#schema_alter_clause.
    def visitSchema_alter_clause(self, ctx:Db2Parser.Schema_alter_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_tag_alter_clause.
    def visitData_tag_alter_clause(self, ctx:Db2Parser.Data_tag_alter_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_workload_statement.
    def visitAlter_workload_statement(self, ctx:Db2Parser.Alter_workload_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_workload_opts_item.
    def visitAlter_workload_opts_item(self, ctx:Db2Parser.Alter_workload_opts_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#package_executable.
    def visitPackage_executable(self, ctx:Db2Parser.Package_executableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#base_none.
    def visitBase_none(self, ctx:Db2Parser.Base_noneContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#extended_base_none.
    def visitExtended_base_none(self, ctx:Db2Parser.Extended_base_noneContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_collect_activity_data_clause.
    def visitAlter_collect_activity_data_clause(self, ctx:Db2Parser.Alter_collect_activity_data_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#with_opts.
    def visitWith_opts(self, ctx:Db2Parser.With_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_collect_history_clause.
    def visitAlter_collect_history_clause(self, ctx:Db2Parser.Alter_collect_history_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_collect_lock_wait_data_clause.
    def visitAlter_collect_lock_wait_data_clause(self, ctx:Db2Parser.Alter_collect_lock_wait_data_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_wrapper_statement.
    def visitAlter_wrapper_statement(self, ctx:Db2Parser.Alter_wrapper_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_wrapper_opts_item.
    def visitAlter_wrapper_opts_item(self, ctx:Db2Parser.Alter_wrapper_opts_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alter_xsrobject_statement.
    def visitAlter_xsrobject_statement(self, ctx:Db2Parser.Alter_xsrobject_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#string.
    def visitString(self, ctx:Db2Parser.StringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#string_constant.
    def visitString_constant(self, ctx:Db2Parser.String_constantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#numeric_constant.
    def visitNumeric_constant(self, ctx:Db2Parser.Numeric_constantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_type.
    def visitData_type(self, ctx:Db2Parser.Data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#anchored_data_type.
    def visitAnchored_data_type(self, ctx:Db2Parser.Anchored_data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#anchored_non_row_data_type.
    def visitAnchored_non_row_data_type(self, ctx:Db2Parser.Anchored_non_row_data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#anchored_row_data_type.
    def visitAnchored_row_data_type(self, ctx:Db2Parser.Anchored_row_data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_data_type.
    def visitSource_data_type(self, ctx:Db2Parser.Source_data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_type_constrainst.
    def visitData_type_constrainst(self, ctx:Db2Parser.Data_type_constrainstContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#check_condition.
    def visitCheck_condition(self, ctx:Db2Parser.Check_conditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_type_2.
    def visitData_type_2(self, ctx:Db2Parser.Data_type_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#built_in_type.
    def visitBuilt_in_type(self, ctx:Db2Parser.Built_in_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#integer_paren.
    def visitInteger_paren(self, ctx:Db2Parser.Integer_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#integer_kmg_paren.
    def visitInteger_kmg_paren(self, ctx:Db2Parser.Integer_kmg_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#char_character.
    def visitChar_character(self, ctx:Db2Parser.Char_characterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#octets_codeunits.
    def visitOctets_codeunits(self, ctx:Db2Parser.Octets_codeunitsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#codeunits.
    def visitCodeunits(self, ctx:Db2Parser.CodeunitsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#kmg.
    def visitKmg(self, ctx:Db2Parser.KmgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#rs_locator_variable.
    def visitRs_locator_variable(self, ctx:Db2Parser.Rs_locator_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#integer_constant_list.
    def visitInteger_constant_list(self, ctx:Db2Parser.Integer_constant_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#integer_constant.
    def visitInteger_constant(self, ctx:Db2Parser.Integer_constantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#integer_value.
    def visitInteger_value(self, ctx:Db2Parser.Integer_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#positive_integer.
    def visitPositive_integer(self, ctx:Db2Parser.Positive_integerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#bigint_value.
    def visitBigint_value(self, ctx:Db2Parser.Bigint_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#bigint_constant.
    def visitBigint_constant(self, ctx:Db2Parser.Bigint_constantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#member_number.
    def visitMember_number(self, ctx:Db2Parser.Member_numberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#version_id.
    def visitVersion_id(self, ctx:Db2Parser.Version_idContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#drop_statement.
    def visitDrop_statement(self, ctx:Db2Parser.Drop_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alias_designator.
    def visitAlias_designator(self, ctx:Db2Parser.Alias_designatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#service_class_designator.
    def visitService_class_designator(self, ctx:Db2Parser.Service_class_designatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tablespace_name_list.
    def visitTablespace_name_list(self, ctx:Db2Parser.Tablespace_name_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#associate_locators_statement.
    def visitAssociate_locators_statement(self, ctx:Db2Parser.Associate_locators_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#audit_statement.
    def visitAudit_statement(self, ctx:Db2Parser.Audit_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#begin_declare_section_statement.
    def visitBegin_declare_section_statement(self, ctx:Db2Parser.Begin_declare_section_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#call_statement.
    def visitCall_statement(self, ctx:Db2Parser.Call_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#arg_list_paren.
    def visitArg_list_paren(self, ctx:Db2Parser.Arg_list_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#arg_list.
    def visitArg_list(self, ctx:Db2Parser.Arg_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#argument.
    def visitArgument(self, ctx:Db2Parser.ArgumentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#case_statement.
    def visitCase_statement(self, ctx:Db2Parser.Case_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#searched_case_statement_when_clause.
    def visitSearched_case_statement_when_clause(self, ctx:Db2Parser.Searched_case_statement_when_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#simple_case_statement_when_clause.
    def visitSimple_case_statement_when_clause(self, ctx:Db2Parser.Simple_case_statement_when_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#close_statement.
    def visitClose_statement(self, ctx:Db2Parser.Close_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#comment_statement.
    def visitComment_statement(self, ctx:Db2Parser.Comment_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_comment.
    def visitColumn_comment(self, ctx:Db2Parser.Column_commentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#comment_objects.
    def visitComment_objects(self, ctx:Db2Parser.Comment_objectsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#commit_statement.
    def visitCommit_statement(self, ctx:Db2Parser.Commit_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#connect_type_1_statement.
    def visitConnect_type_1_statement(self, ctx:Db2Parser.Connect_type_1_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#authorization.
    def visitAuthorization(self, ctx:Db2Parser.AuthorizationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#passwords.
    def visitPasswords(self, ctx:Db2Parser.PasswordsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#lock_block.
    def visitLock_block(self, ctx:Db2Parser.Lock_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#accesstoken.
    def visitAccesstoken(self, ctx:Db2Parser.AccesstokenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#token.
    def visitToken(self, ctx:Db2Parser.TokenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#api_key.
    def visitApi_key(self, ctx:Db2Parser.Api_keyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#token_type.
    def visitToken_type(self, ctx:Db2Parser.Token_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#declare_cursor_statement.
    def visitDeclare_cursor_statement(self, ctx:Db2Parser.Declare_cursor_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#declare_global_temporary_table_statement.
    def visitDeclare_global_temporary_table_statement(self, ctx:Db2Parser.Declare_global_temporary_table_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#describe_statement.
    def visitDescribe_statement(self, ctx:Db2Parser.Describe_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#xquery_statement.
    def visitXquery_statement(self, ctx:Db2Parser.Xquery_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#describe_input_statement.
    def visitDescribe_input_statement(self, ctx:Db2Parser.Describe_input_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#describe_output_statement.
    def visitDescribe_output_statement(self, ctx:Db2Parser.Describe_output_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#disconnect_statement.
    def visitDisconnect_statement(self, ctx:Db2Parser.Disconnect_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#end_declare_section_statement.
    def visitEnd_declare_section_statement(self, ctx:Db2Parser.End_declare_section_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#execute_statement.
    def visitExecute_statement(self, ctx:Db2Parser.Execute_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#host_variable_expression.
    def visitHost_variable_expression(self, ctx:Db2Parser.Host_variable_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#assignment_target.
    def visitAssignment_target(self, ctx:Db2Parser.Assignment_targetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#execute_immediate_statement.
    def visitExecute_immediate_statement(self, ctx:Db2Parser.Execute_immediate_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#explain_statement.
    def visitExplain_statement(self, ctx:Db2Parser.Explain_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#explainable_sql_statement.
    def visitExplainable_sql_statement(self, ctx:Db2Parser.Explainable_sql_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#fetch_statement.
    def visitFetch_statement(self, ctx:Db2Parser.Fetch_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#flush_bufferpools_statement.
    def visitFlush_bufferpools_statement(self, ctx:Db2Parser.Flush_bufferpools_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#flush_event_monitor_statement.
    def visitFlush_event_monitor_statement(self, ctx:Db2Parser.Flush_event_monitor_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#flush_federated_cache_statement.
    def visitFlush_federated_cache_statement(self, ctx:Db2Parser.Flush_federated_cache_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#flush_optimization_profile_cache_statement.
    def visitFlush_optimization_profile_cache_statement(self, ctx:Db2Parser.Flush_optimization_profile_cache_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#flush_package_cache_statement.
    def visitFlush_package_cache_statement(self, ctx:Db2Parser.Flush_package_cache_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#flush_authentication_cache_statement.
    def visitFlush_authentication_cache_statement(self, ctx:Db2Parser.Flush_authentication_cache_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#free_locator_statement.
    def visitFree_locator_statement(self, ctx:Db2Parser.Free_locator_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#get_diagnostics_statement.
    def visitGet_diagnostics_statement(self, ctx:Db2Parser.Get_diagnostics_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#statement_information.
    def visitStatement_information(self, ctx:Db2Parser.Statement_informationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#condition_information.
    def visitCondition_information(self, ctx:Db2Parser.Condition_informationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#condition_var_assignment.
    def visitCondition_var_assignment(self, ctx:Db2Parser.Condition_var_assignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#lock_table_statement.
    def visitLock_table_statement(self, ctx:Db2Parser.Lock_table_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#pipe_statement.
    def visitPipe_statement(self, ctx:Db2Parser.Pipe_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#refresh_table_statement.
    def visitRefresh_table_statement(self, ctx:Db2Parser.Refresh_table_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#release_connection_statement.
    def visitRelease_connection_statement(self, ctx:Db2Parser.Release_connection_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#rename_statement.
    def visitRename_statement(self, ctx:Db2Parser.Rename_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#rename_stogroup_statement.
    def visitRename_stogroup_statement(self, ctx:Db2Parser.Rename_stogroup_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#rename_tablespace_statement.
    def visitRename_tablespace_statement(self, ctx:Db2Parser.Rename_tablespace_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#set_statement.
    def visitSet_statement(self, ctx:Db2Parser.Set_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#access_mode_clause.
    def visitAccess_mode_clause(self, ctx:Db2Parser.Access_mode_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#cascade_clause.
    def visitCascade_clause(self, ctx:Db2Parser.Cascade_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#to_descendent_types.
    def visitTo_descendent_types(self, ctx:Db2Parser.To_descendent_typesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_type_list.
    def visitTable_type_list(self, ctx:Db2Parser.Table_type_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_type.
    def visitTable_type(self, ctx:Db2Parser.Table_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_checked_options_list.
    def visitTable_checked_options_list(self, ctx:Db2Parser.Table_checked_options_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_checked_options.
    def visitTable_checked_options(self, ctx:Db2Parser.Table_checked_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#online_options.
    def visitOnline_options(self, ctx:Db2Parser.Online_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#query_optimization_options.
    def visitQuery_optimization_options(self, ctx:Db2Parser.Query_optimization_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#check_options.
    def visitCheck_options(self, ctx:Db2Parser.Check_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#incremental_options.
    def visitIncremental_options(self, ctx:Db2Parser.Incremental_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#exception_clause.
    def visitException_clause(self, ctx:Db2Parser.Exception_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#in_table_use_clause.
    def visitIn_table_use_clause(self, ctx:Db2Parser.In_table_use_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_unchecked_options.
    def visitTable_unchecked_options(self, ctx:Db2Parser.Table_unchecked_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#full_access.
    def visitFull_access(self, ctx:Db2Parser.Full_accessContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#integrity_options.
    def visitIntegrity_options(self, ctx:Db2Parser.Integrity_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#integrity_options_item.
    def visitIntegrity_options_item(self, ctx:Db2Parser.Integrity_options_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#var_def_list.
    def visitVar_def_list(self, ctx:Db2Parser.Var_def_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#var_def.
    def visitVar_def(self, ctx:Db2Parser.Var_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#expr_null.
    def visitExpr_null(self, ctx:Db2Parser.Expr_nullContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#expr_null_default.
    def visitExpr_null_default(self, ctx:Db2Parser.Expr_null_defaultContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#array_index.
    def visitArray_index(self, ctx:Db2Parser.Array_indexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_fullselect.
    def visitRow_fullselect(self, ctx:Db2Parser.Row_fullselectContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#target_variable.
    def visitTarget_variable(self, ctx:Db2Parser.Target_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#target_cursor_variable.
    def visitTarget_cursor_variable(self, ctx:Db2Parser.Target_cursor_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#target_row_variable.
    def visitTarget_row_variable(self, ctx:Db2Parser.Target_row_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_array_element_specification.
    def visitRow_array_element_specification(self, ctx:Db2Parser.Row_array_element_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_field_reference.
    def visitRow_field_reference(self, ctx:Db2Parser.Row_field_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#field_reference.
    def visitField_reference(self, ctx:Db2Parser.Field_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#search_condition.
    def visitSearch_condition(self, ctx:Db2Parser.Search_conditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#predicate.
    def visitPredicate(self, ctx:Db2Parser.PredicateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#according_to_clause.
    def visitAccording_to_clause(self, ctx:Db2Parser.According_to_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#xml_schema_identification_list.
    def visitXml_schema_identification_list(self, ctx:Db2Parser.Xml_schema_identification_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#xml_schema_identification.
    def visitXml_schema_identification(self, ctx:Db2Parser.Xml_schema_identificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#fullselect_in_parentheses.
    def visitFullselect_in_parentheses(self, ctx:Db2Parser.Fullselect_in_parenthesesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#some_any_all.
    def visitSome_any_all(self, ctx:Db2Parser.Some_any_allContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_value_expression.
    def visitRow_value_expression(self, ctx:Db2Parser.Row_value_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#comparison_operator.
    def visitComparison_operator(self, ctx:Db2Parser.Comparison_operatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_expression.
    def visitRow_expression(self, ctx:Db2Parser.Row_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#path_opt_list.
    def visitPath_opt_list(self, ctx:Db2Parser.Path_opt_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#path_opt.
    def visitPath_opt(self, ctx:Db2Parser.Path_optContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#pkg_opt_list.
    def visitPkg_opt_list(self, ctx:Db2Parser.Pkg_opt_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#pkg_opt.
    def visitPkg_opt(self, ctx:Db2Parser.Pkg_optContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#maintain_opt_list.
    def visitMaintain_opt_list(self, ctx:Db2Parser.Maintain_opt_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#maintain_opt.
    def visitMaintain_opt(self, ctx:Db2Parser.Maintain_optContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#variable.
    def visitVariable(self, ctx:Db2Parser.VariableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#host_variable.
    def visitHost_variable(self, ctx:Db2Parser.Host_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#set_integrity_statement.
    def visitSet_integrity_statement(self, ctx:Db2Parser.Set_integrity_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#transfer_ownership_statement.
    def visitTransfer_ownership_statement(self, ctx:Db2Parser.Transfer_ownership_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#objects.
    def visitObjects(self, ctx:Db2Parser.ObjectsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#whenever_statement.
    def visitWhenever_statement(self, ctx:Db2Parser.Whenever_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#for_statement.
    def visitFor_statement(self, ctx:Db2Parser.For_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#goto_statement.
    def visitGoto_statement(self, ctx:Db2Parser.Goto_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#if_statement.
    def visitIf_statement(self, ctx:Db2Parser.If_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#include_statement.
    def visitInclude_statement(self, ctx:Db2Parser.Include_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#resignal_statement.
    def visitResignal_statement(self, ctx:Db2Parser.Resignal_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#signal_information.
    def visitSignal_information(self, ctx:Db2Parser.Signal_informationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#diagnostic_string_constant.
    def visitDiagnostic_string_constant(self, ctx:Db2Parser.Diagnostic_string_constantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#signal_statement.
    def visitSignal_statement(self, ctx:Db2Parser.Signal_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sqlstate_string_constant.
    def visitSqlstate_string_constant(self, ctx:Db2Parser.Sqlstate_string_constantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sqlstate_string_variable.
    def visitSqlstate_string_variable(self, ctx:Db2Parser.Sqlstate_string_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#signal_information_2.
    def visitSignal_information_2(self, ctx:Db2Parser.Signal_information_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#diagnostic_string_expression.
    def visitDiagnostic_string_expression(self, ctx:Db2Parser.Diagnostic_string_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#iterate_statement.
    def visitIterate_statement(self, ctx:Db2Parser.Iterate_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#leave_statement.
    def visitLeave_statement(self, ctx:Db2Parser.Leave_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#loop_statement.
    def visitLoop_statement(self, ctx:Db2Parser.Loop_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#open_statement.
    def visitOpen_statement(self, ctx:Db2Parser.Open_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#variable_or_expression.
    def visitVariable_or_expression(self, ctx:Db2Parser.Variable_or_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#select_into_statement.
    def visitSelect_into_statement(self, ctx:Db2Parser.Select_into_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#values_into_statement.
    def visitValues_into_statement(self, ctx:Db2Parser.Values_into_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#prepare_statement.
    def visitPrepare_statement(self, ctx:Db2Parser.Prepare_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#repeat_statement.
    def visitRepeat_statement(self, ctx:Db2Parser.Repeat_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#return_statement.
    def visitReturn_statement(self, ctx:Db2Parser.Return_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#while_statement.
    def visitWhile_statement(self, ctx:Db2Parser.While_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_routine_statement.
    def visitSql_routine_statement(self, ctx:Db2Parser.Sql_routine_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#common_table_expression.
    def visitCommon_table_expression(self, ctx:Db2Parser.Common_table_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_alias_statement.
    def visitCreate_alias_statement(self, ctx:Db2Parser.Create_alias_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_alias.
    def visitTable_alias(self, ctx:Db2Parser.Table_aliasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_alias.
    def visitModule_alias(self, ctx:Db2Parser.Module_aliasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sequence_alias.
    def visitSequence_alias(self, ctx:Db2Parser.Sequence_aliasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#or_replace.
    def visitOr_replace(self, ctx:Db2Parser.Or_replaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_audit_policy_statement.
    def visitCreate_audit_policy_statement(self, ctx:Db2Parser.Create_audit_policy_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#audit_policy_opts.
    def visitAudit_policy_opts(self, ctx:Db2Parser.Audit_policy_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#audit_policy_categories_opts.
    def visitAudit_policy_categories_opts(self, ctx:Db2Parser.Audit_policy_categories_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_bufferpool_statement.
    def visitCreate_bufferpool_statement(self, ctx:Db2Parser.Create_bufferpool_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#bufferpool_opts.
    def visitBufferpool_opts(self, ctx:Db2Parser.Bufferpool_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#except_clause.
    def visitExcept_clause(self, ctx:Db2Parser.Except_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#member_list.
    def visitMember_list(self, ctx:Db2Parser.Member_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#member_list_item.
    def visitMember_list_item(self, ctx:Db2Parser.Member_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_database_partition_group_statement.
    def visitCreate_database_partition_group_statement(self, ctx:Db2Parser.Create_database_partition_group_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_event_monitor_statement.
    def visitCreate_event_monitor_statement(self, ctx:Db2Parser.Create_event_monitor_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_event_monitor_activities_statement.
    def visitCreate_event_monitor_activities_statement(self, ctx:Db2Parser.Create_event_monitor_activities_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#formatted_event_table_info_3.
    def visitFormatted_event_table_info_3(self, ctx:Db2Parser.Formatted_event_table_info_3Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_event_monitor_change_history_statement.
    def visitCreate_event_monitor_change_history_statement(self, ctx:Db2Parser.Create_event_monitor_change_history_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#event_control_list.
    def visitEvent_control_list(self, ctx:Db2Parser.Event_control_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#event_control.
    def visitEvent_control(self, ctx:Db2Parser.Event_controlContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_event_monitor_locking_statement.
    def visitCreate_event_monitor_locking_statement(self, ctx:Db2Parser.Create_event_monitor_locking_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_event_monitor_package_cache_statement.
    def visitCreate_event_monitor_package_cache_statement(self, ctx:Db2Parser.Create_event_monitor_package_cache_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#filter_and_collection_options.
    def visitFilter_and_collection_options(self, ctx:Db2Parser.Filter_and_collection_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#event_condition.
    def visitEvent_condition(self, ctx:Db2Parser.Event_conditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#event_condition_item.
    def visitEvent_condition_item(self, ctx:Db2Parser.Event_condition_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_event_monitor_statistics_statement.
    def visitCreate_event_monitor_statistics_statement(self, ctx:Db2Parser.Create_event_monitor_statistics_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#event_monitor_statistics_opts.
    def visitEvent_monitor_statistics_opts(self, ctx:Db2Parser.Event_monitor_statistics_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_event_monitor_threshold_violations_statement.
    def visitCreate_event_monitor_threshold_violations_statement(self, ctx:Db2Parser.Create_event_monitor_threshold_violations_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#formatted_event_table_info_2.
    def visitFormatted_event_table_info_2(self, ctx:Db2Parser.Formatted_event_table_info_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#file_options.
    def visitFile_options(self, ctx:Db2Parser.File_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#event_monitor_threshold_opts.
    def visitEvent_monitor_threshold_opts(self, ctx:Db2Parser.Event_monitor_threshold_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#pages.
    def visitPages(self, ctx:Db2Parser.PagesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_event_monitor_unit_of_work.
    def visitCreate_event_monitor_unit_of_work(self, ctx:Db2Parser.Create_event_monitor_unit_of_workContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#formatted_event_table_info.
    def visitFormatted_event_table_info(self, ctx:Db2Parser.Formatted_event_table_infoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#autostart_manualstart.
    def visitAutostart_manualstart(self, ctx:Db2Parser.Autostart_manualstartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#evm_group.
    def visitEvm_group(self, ctx:Db2Parser.Evm_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#target_table_options.
    def visitTarget_table_options(self, ctx:Db2Parser.Target_table_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_external_table_statement.
    def visitCreate_external_table_statement(self, ctx:Db2Parser.Create_external_table_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ext_table_option.
    def visitExt_table_option(self, ctx:Db2Parser.Ext_table_optionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ext_table_option_value.
    def visitExt_table_option_value(self, ctx:Db2Parser.Ext_table_option_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_function_statement.
    def visitCreate_function_statement(self, ctx:Db2Parser.Create_function_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_function_aggregate_interface_statement.
    def visitCreate_function_aggregate_interface_statement(self, ctx:Db2Parser.Create_function_aggregate_interface_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#agg_fn_param_decl.
    def visitAgg_fn_param_decl(self, ctx:Db2Parser.Agg_fn_param_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#agg_fn_option_list.
    def visitAgg_fn_option_list(self, ctx:Db2Parser.Agg_fn_option_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#state_variable_declaration.
    def visitState_variable_declaration(self, ctx:Db2Parser.State_variable_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_function_external_scalar_statement.
    def visitCreate_function_external_scalar_statement(self, ctx:Db2Parser.Create_function_external_scalar_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ext_scalar_param_decl.
    def visitExt_scalar_param_decl(self, ctx:Db2Parser.Ext_scalar_param_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ext_scalar_option_list.
    def visitExt_scalar_option_list(self, ctx:Db2Parser.Ext_scalar_option_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ext_scalar_option_list_item.
    def visitExt_scalar_option_list_item(self, ctx:Db2Parser.Ext_scalar_option_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#predicate_specification.
    def visitPredicate_specification(self, ctx:Db2Parser.Predicate_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_filter.
    def visitData_filter(self, ctx:Db2Parser.Data_filterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#index_exploitation.
    def visitIndex_exploitation(self, ctx:Db2Parser.Index_exploitationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#exploitation_rule.
    def visitExploitation_rule(self, ctx:Db2Parser.Exploitation_ruleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_function_external_table_statement.
    def visitCreate_function_external_table_statement(self, ctx:Db2Parser.Create_function_external_table_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ext_table_param_decl_list.
    def visitExt_table_param_decl_list(self, ctx:Db2Parser.Ext_table_param_decl_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ext_table_param_decl.
    def visitExt_table_param_decl(self, ctx:Db2Parser.Ext_table_param_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ext_table_option_list.
    def visitExt_table_option_list(self, ctx:Db2Parser.Ext_table_option_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ext_table_option_list_item.
    def visitExt_table_option_list_item(self, ctx:Db2Parser.Ext_table_option_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_function_old_db_external_function_statement.
    def visitCreate_function_old_db_external_function_statement(self, ctx:Db2Parser.Create_function_old_db_external_function_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#oledb_option_list.
    def visitOledb_option_list(self, ctx:Db2Parser.Oledb_option_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#oledb_option_list_item.
    def visitOledb_option_list_item(self, ctx:Db2Parser.Oledb_option_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_function_sourced_or_template_statement.
    def visitCreate_function_sourced_or_template_statement(self, ctx:Db2Parser.Create_function_sourced_or_template_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#fn_return_opts.
    def visitFn_return_opts(self, ctx:Db2Parser.Fn_return_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#fn_return_opts_item.
    def visitFn_return_opts_item(self, ctx:Db2Parser.Fn_return_opts_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#template_opts.
    def visitTemplate_opts(self, ctx:Db2Parser.Template_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#template_opts_item.
    def visitTemplate_opts_item(self, ctx:Db2Parser.Template_opts_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ascii_unicode.
    def visitAscii_unicode(self, ctx:Db2Parser.Ascii_unicodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#param_decl_list_3.
    def visitParam_decl_list_3(self, ctx:Db2Parser.Param_decl_list_3Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#param_decl_3.
    def visitParam_decl_3(self, ctx:Db2Parser.Param_decl_3Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_function_sql_scalar_table_or_row_statement.
    def visitCreate_function_sql_scalar_table_or_row_statement(self, ctx:Db2Parser.Create_function_sql_scalar_table_or_row_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#param_decl_list_2.
    def visitParam_decl_list_2(self, ctx:Db2Parser.Param_decl_list_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#param_decl_2.
    def visitParam_decl_2(self, ctx:Db2Parser.Param_decl_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_function_body.
    def visitSql_function_body(self, ctx:Db2Parser.Sql_function_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_function_mapping_statement.
    def visitCreate_function_mapping_statement(self, ctx:Db2Parser.Create_function_mapping_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#function_options.
    def visitFunction_options(self, ctx:Db2Parser.Function_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#function_option_name.
    def visitFunction_option_name(self, ctx:Db2Parser.Function_option_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_global_temporary_table_statement.
    def visitCreate_global_temporary_table_statement(self, ctx:Db2Parser.Create_global_temporary_table_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_global_temporary_table_opts.
    def visitCreate_global_temporary_table_opts(self, ctx:Db2Parser.Create_global_temporary_table_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_global_temporary_table_item.
    def visitCreate_global_temporary_table_item(self, ctx:Db2Parser.Create_global_temporary_table_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#delete_preserve.
    def visitDelete_preserve(self, ctx:Db2Parser.Delete_preserveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_histogram_template_statement.
    def visitCreate_histogram_template_statement(self, ctx:Db2Parser.Create_histogram_template_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_index_statement.
    def visitCreate_index_statement(self, ctx:Db2Parser.Create_index_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#index_col_opts.
    def visitIndex_col_opts(self, ctx:Db2Parser.Index_col_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#index_col_opts_item.
    def visitIndex_col_opts_item(self, ctx:Db2Parser.Index_col_opts_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#key_expression.
    def visitKey_expression(self, ctx:Db2Parser.Key_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_index_extension_statement.
    def visitCreate_index_extension_statement(self, ctx:Db2Parser.Create_index_extension_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#param_list.
    def visitParam_list(self, ctx:Db2Parser.Param_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#index_maintenance.
    def visitIndex_maintenance(self, ctx:Db2Parser.Index_maintenanceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_function_invocation.
    def visitTable_function_invocation(self, ctx:Db2Parser.Table_function_invocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#index_search.
    def visitIndex_search(self, ctx:Db2Parser.Index_searchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#search_method_definition.
    def visitSearch_method_definition(self, ctx:Db2Parser.Search_method_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_mask_statement.
    def visitCreate_mask_statement(self, ctx:Db2Parser.Create_mask_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#case_expression.
    def visitCase_expression(self, ctx:Db2Parser.Case_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#range_producing_funciton_invocation.
    def visitRange_producing_funciton_invocation(self, ctx:Db2Parser.Range_producing_funciton_invocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#index_filtering_function_invocation.
    def visitIndex_filtering_function_invocation(self, ctx:Db2Parser.Index_filtering_function_invocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_method_statement.
    def visitCreate_method_statement(self, ctx:Db2Parser.Create_method_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_opts.
    def visitMethod_opts(self, ctx:Db2Parser.Method_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_opts_item.
    def visitMethod_opts_item(self, ctx:Db2Parser.Method_opts_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_signature.
    def visitMethod_signature(self, ctx:Db2Parser.Method_signatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_param_list.
    def visitMethod_param_list(self, ctx:Db2Parser.Method_param_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_type_3.
    def visitData_type_3(self, ctx:Db2Parser.Data_type_3Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_type_4.
    def visitData_type_4(self, ctx:Db2Parser.Data_type_4Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_method_body.
    def visitSql_method_body(self, ctx:Db2Parser.Sql_method_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#compound_sql_inlined.
    def visitCompound_sql_inlined(self, ctx:Db2Parser.Compound_sql_inlinedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_statement_inlined.
    def visitSql_statement_inlined(self, ctx:Db2Parser.Sql_statement_inlinedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#compound_sql_compiled.
    def visitCompound_sql_compiled(self, ctx:Db2Parser.Compound_sql_compiledContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_statement_compiled.
    def visitSql_statement_compiled(self, ctx:Db2Parser.Sql_statement_compiledContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_module_statement.
    def visitCreate_module_statement(self, ctx:Db2Parser.Create_module_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_nickname_statement.
    def visitCreate_nickname_statement(self, ctx:Db2Parser.Create_nickname_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#nick_name_option_name.
    def visitNick_name_option_name(self, ctx:Db2Parser.Nick_name_option_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#remote_object_name.
    def visitRemote_object_name(self, ctx:Db2Parser.Remote_object_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#non_relational_data_definition.
    def visitNon_relational_data_definition(self, ctx:Db2Parser.Non_relational_data_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#nick_name_column_list.
    def visitNick_name_column_list(self, ctx:Db2Parser.Nick_name_column_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#nick_name_column_list_item.
    def visitNick_name_column_list_item(self, ctx:Db2Parser.Nick_name_column_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#nick_name_column_definition.
    def visitNick_name_column_definition(self, ctx:Db2Parser.Nick_name_column_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#nick_name_column_options.
    def visitNick_name_column_options(self, ctx:Db2Parser.Nick_name_column_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#federated_column_options.
    def visitFederated_column_options(self, ctx:Db2Parser.Federated_column_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_option_name.
    def visitColumn_option_name(self, ctx:Db2Parser.Column_option_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_permission_statement.
    def visitCreate_permission_statement(self, ctx:Db2Parser.Create_permission_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_procedure_statement.
    def visitCreate_procedure_statement(self, ctx:Db2Parser.Create_procedure_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_procedure_external_statement.
    def visitCreate_procedure_external_statement(self, ctx:Db2Parser.Create_procedure_external_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#proc_ext_param_list.
    def visitProc_ext_param_list(self, ctx:Db2Parser.Proc_ext_param_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#proc_ext_param.
    def visitProc_ext_param(self, ctx:Db2Parser.Proc_ext_paramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#option_list_2.
    def visitOption_list_2(self, ctx:Db2Parser.Option_list_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#option_list_2_item.
    def visitOption_list_2_item(self, ctx:Db2Parser.Option_list_2_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_procedure_sourced_statement.
    def visitCreate_procedure_sourced_statement(self, ctx:Db2Parser.Create_procedure_sourced_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_procedure_clause.
    def visitSource_procedure_clause(self, ctx:Db2Parser.Source_procedure_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_object_name.
    def visitSource_object_name(self, ctx:Db2Parser.Source_object_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#option_list_1.
    def visitOption_list_1(self, ctx:Db2Parser.Option_list_1Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#option_list_1_item.
    def visitOption_list_1_item(self, ctx:Db2Parser.Option_list_1_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#result_set_element_number.
    def visitResult_set_element_number(self, ctx:Db2Parser.Result_set_element_numberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#unique_id.
    def visitUnique_id(self, ctx:Db2Parser.Unique_idContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_procedure_sql_statement.
    def visitCreate_procedure_sql_statement(self, ctx:Db2Parser.Create_procedure_sql_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#proc_parameter_list.
    def visitProc_parameter_list(self, ctx:Db2Parser.Proc_parameter_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#proc_parameter_list_item.
    def visitProc_parameter_list_item(self, ctx:Db2Parser.Proc_parameter_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#in_out_inout.
    def visitIn_out_inout(self, ctx:Db2Parser.In_out_inoutContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#option_list.
    def visitOption_list(self, ctx:Db2Parser.Option_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#option_list_item.
    def visitOption_list_item(self, ctx:Db2Parser.Option_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_procedure_body.
    def visitSql_procedure_body(self, ctx:Db2Parser.Sql_procedure_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_role_statement.
    def visitCreate_role_statement(self, ctx:Db2Parser.Create_role_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_schema_statement.
    def visitCreate_schema_statement(self, ctx:Db2Parser.Create_schema_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#schema_sql_statement.
    def visitSchema_sql_statement(self, ctx:Db2Parser.Schema_sql_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_security_label_component_statement.
    def visitCreate_security_label_component_statement(self, ctx:Db2Parser.Create_security_label_component_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#array_clause.
    def visitArray_clause(self, ctx:Db2Parser.Array_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#set_clause.
    def visitSet_clause(self, ctx:Db2Parser.Set_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tree_clause.
    def visitTree_clause(self, ctx:Db2Parser.Tree_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tree_clause_item.
    def visitTree_clause_item(self, ctx:Db2Parser.Tree_clause_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_security_label_statement.
    def visitCreate_security_label_statement(self, ctx:Db2Parser.Create_security_label_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_security_label_item.
    def visitCreate_security_label_item(self, ctx:Db2Parser.Create_security_label_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_security_policy_statement.
    def visitCreate_security_policy_statement(self, ctx:Db2Parser.Create_security_policy_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_sequence_statement.
    def visitCreate_sequence_statement(self, ctx:Db2Parser.Create_sequence_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_sequence_opts.
    def visitCreate_sequence_opts(self, ctx:Db2Parser.Create_sequence_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_sequence_opts_item.
    def visitCreate_sequence_opts_item(self, ctx:Db2Parser.Create_sequence_opts_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_service_class_statement.
    def visitCreate_service_class_statement(self, ctx:Db2Parser.Create_service_class_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#high_medium_low.
    def visitHigh_medium_low(self, ctx:Db2Parser.High_medium_lowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#on_off.
    def visitOn_off(self, ctx:Db2Parser.On_offContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#soft_hard.
    def visitSoft_hard(self, ctx:Db2Parser.Soft_hardContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_server_statement.
    def visitCreate_server_statement(self, ctx:Db2Parser.Create_server_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#password_.
    def visitPassword_(self, ctx:Db2Parser.Password_Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_stogroup_statement.
    def visitCreate_stogroup_statement(self, ctx:Db2Parser.Create_stogroup_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_stogroup_opts.
    def visitCreate_stogroup_opts(self, ctx:Db2Parser.Create_stogroup_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_synonym_statement.
    def visitCreate_synonym_statement(self, ctx:Db2Parser.Create_synonym_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_table_statement.
    def visitCreate_table_statement(self, ctx:Db2Parser.Create_table_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_table_opts.
    def visitCreate_table_opts(self, ctx:Db2Parser.Create_table_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_option_list.
    def visitTable_option_list(self, ctx:Db2Parser.Table_option_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_option_list_item.
    def visitTable_option_list_item(self, ctx:Db2Parser.Table_option_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_option_name.
    def visitTable_option_name(self, ctx:Db2Parser.Table_option_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#element_list.
    def visitElement_list(self, ctx:Db2Parser.Element_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#element_list_item.
    def visitElement_list_item(self, ctx:Db2Parser.Element_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_definition.
    def visitColumn_definition(self, ctx:Db2Parser.Column_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#period_definition.
    def visitPeriod_definition(self, ctx:Db2Parser.Period_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#unique_constraint.
    def visitUnique_constraint(self, ctx:Db2Parser.Unique_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#referential_constraint.
    def visitReferential_constraint(self, ctx:Db2Parser.Referential_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#check_constraint.
    def visitCheck_constraint(self, ctx:Db2Parser.Check_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_options.
    def visitColumn_options(self, ctx:Db2Parser.Column_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_options_item.
    def visitColumn_options_item(self, ctx:Db2Parser.Column_options_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#references_clause.
    def visitReferences_clause(self, ctx:Db2Parser.References_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#rule_clause.
    def visitRule_clause(self, ctx:Db2Parser.Rule_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#constraint_attributes.
    def visitConstraint_attributes(self, ctx:Db2Parser.Constraint_attributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#default_clause.
    def visitDefault_clause(self, ctx:Db2Parser.Default_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#default_values.
    def visitDefault_values(self, ctx:Db2Parser.Default_valuesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#generated_clause.
    def visitGenerated_clause(self, ctx:Db2Parser.Generated_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#datetime_special_register.
    def visitDatetime_special_register(self, ctx:Db2Parser.Datetime_special_registerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#user_special_register.
    def visitUser_special_register(self, ctx:Db2Parser.User_special_registerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#cast_function.
    def visitCast_function(self, ctx:Db2Parser.Cast_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#identity_options.
    def visitIdentity_options(self, ctx:Db2Parser.Identity_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#identity_options_item.
    def visitIdentity_options_item(self, ctx:Db2Parser.Identity_options_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#as_row_change_timestamp_clause.
    def visitAs_row_change_timestamp_clause(self, ctx:Db2Parser.As_row_change_timestamp_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#as_generated_expression_clause.
    def visitAs_generated_expression_clause(self, ctx:Db2Parser.As_generated_expression_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#generation_expression.
    def visitGeneration_expression(self, ctx:Db2Parser.Generation_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#as_row_transaction_timestamp_clause.
    def visitAs_row_transaction_timestamp_clause(self, ctx:Db2Parser.As_row_transaction_timestamp_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#as_row_transaction_start_id_clause.
    def visitAs_row_transaction_start_id_clause(self, ctx:Db2Parser.As_row_transaction_start_id_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#oid_column_definition.
    def visitOid_column_definition(self, ctx:Db2Parser.Oid_column_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#range_partition_spec.
    def visitRange_partition_spec(self, ctx:Db2Parser.Range_partition_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#partition_expression_list.
    def visitPartition_expression_list(self, ctx:Db2Parser.Partition_expression_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#partition_expression.
    def visitPartition_expression(self, ctx:Db2Parser.Partition_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#partition_element_list.
    def visitPartition_element_list(self, ctx:Db2Parser.Partition_element_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#partition_element.
    def visitPartition_element(self, ctx:Db2Parser.Partition_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#boundary_spec.
    def visitBoundary_spec(self, ctx:Db2Parser.Boundary_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#partition_tablespace_options.
    def visitPartition_tablespace_options(self, ctx:Db2Parser.Partition_tablespace_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#duration_label.
    def visitDuration_label(self, ctx:Db2Parser.Duration_labelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#starting_clause.
    def visitStarting_clause(self, ctx:Db2Parser.Starting_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#const_min_max_list.
    def visitConst_min_max_list(self, ctx:Db2Parser.Const_min_max_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#const_min_max.
    def visitConst_min_max(self, ctx:Db2Parser.Const_min_maxContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ending_clause.
    def visitEnding_clause(self, ctx:Db2Parser.Ending_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#typed_table_options.
    def visitTyped_table_options(self, ctx:Db2Parser.Typed_table_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#typed_element_list.
    def visitTyped_element_list(self, ctx:Db2Parser.Typed_element_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#typed_element_list_item.
    def visitTyped_element_list_item(self, ctx:Db2Parser.Typed_element_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#as_result_table.
    def visitAs_result_table(self, ctx:Db2Parser.As_result_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#copy_options.
    def visitCopy_options(self, ctx:Db2Parser.Copy_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#materialized_query_options.
    def visitMaterialized_query_options(self, ctx:Db2Parser.Materialized_query_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#staging_table_definition.
    def visitStaging_table_definition(self, ctx:Db2Parser.Staging_table_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#dimensions_clause.
    def visitDimensions_clause(self, ctx:Db2Parser.Dimensions_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#col_names.
    def visitCol_names(self, ctx:Db2Parser.Col_namesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sequence_key_spec.
    def visitSequence_key_spec(self, ctx:Db2Parser.Sequence_key_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sequence_key_spec_list.
    def visitSequence_key_spec_list(self, ctx:Db2Parser.Sequence_key_spec_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sequence_key_spec_list_item.
    def visitSequence_key_spec_list_item(self, ctx:Db2Parser.Sequence_key_spec_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tablespace_clauses.
    def visitTablespace_clauses(self, ctx:Db2Parser.Tablespace_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#distribution_clause.
    def visitDistribution_clause(self, ctx:Db2Parser.Distribution_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#partitioning_clause.
    def visitPartitioning_clause(self, ctx:Db2Parser.Partitioning_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#if_not_exists.
    def visitIf_not_exists(self, ctx:Db2Parser.If_not_existsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_tablespace_statement.
    def visitCreate_tablespace_statement(self, ctx:Db2Parser.Create_tablespace_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#storage_group.
    def visitStorage_group(self, ctx:Db2Parser.Storage_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#size_attributes.
    def visitSize_attributes(self, ctx:Db2Parser.Size_attributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#system_containers.
    def visitSystem_containers(self, ctx:Db2Parser.System_containersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#container_string_list.
    def visitContainer_string_list(self, ctx:Db2Parser.Container_string_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#database_containers.
    def visitDatabase_containers(self, ctx:Db2Parser.Database_containersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#container_clause.
    def visitContainer_clause(self, ctx:Db2Parser.Container_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#container_clause_list.
    def visitContainer_clause_list(self, ctx:Db2Parser.Container_clause_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#container_clause_list_item.
    def visitContainer_clause_list_item(self, ctx:Db2Parser.Container_clause_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#on_db_partitions_clause.
    def visitOn_db_partitions_clause(self, ctx:Db2Parser.On_db_partitions_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_partition_number_list.
    def visitDb_partition_number_list(self, ctx:Db2Parser.Db_partition_number_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_partition_number_list_item.
    def visitDb_partition_number_list_item(self, ctx:Db2Parser.Db_partition_number_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_partition_number.
    def visitDb_partition_number(self, ctx:Db2Parser.Db_partition_numberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#number_of_pages.
    def visitNumber_of_pages(self, ctx:Db2Parser.Number_of_pagesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#number_of_files.
    def visitNumber_of_files(self, ctx:Db2Parser.Number_of_filesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#number_of_milliseconds.
    def visitNumber_of_milliseconds(self, ctx:Db2Parser.Number_of_millisecondsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#number_megabytes_per_second.
    def visitNumber_megabytes_per_second(self, ctx:Db2Parser.Number_megabytes_per_secondContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_threshold_statement.
    def visitCreate_threshold_statement(self, ctx:Db2Parser.Create_threshold_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#threshold_domain.
    def visitThreshold_domain(self, ctx:Db2Parser.Threshold_domainContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#statement_text.
    def visitStatement_text(self, ctx:Db2Parser.Statement_textContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#executable_id.
    def visitExecutable_id(self, ctx:Db2Parser.Executable_idContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#enforcement_scope.
    def visitEnforcement_scope(self, ctx:Db2Parser.Enforcement_scopeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#threshold_predicate.
    def visitThreshold_predicate(self, ctx:Db2Parser.Threshold_predicateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#checking_every.
    def visitChecking_every(self, ctx:Db2Parser.Checking_everyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#hour_to_seconds.
    def visitHour_to_seconds(self, ctx:Db2Parser.Hour_to_secondsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#day_to_minutes.
    def visitDay_to_minutes(self, ctx:Db2Parser.Day_to_minutesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#day_to_seconds.
    def visitDay_to_seconds(self, ctx:Db2Parser.Day_to_secondsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#threshold_exceeded_actions_2.
    def visitThreshold_exceeded_actions_2(self, ctx:Db2Parser.Threshold_exceeded_actions_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#details_section.
    def visitDetails_section(self, ctx:Db2Parser.Details_sectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#remap_activity_action.
    def visitRemap_activity_action(self, ctx:Db2Parser.Remap_activity_actionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_transform_statement.
    def visitCreate_transform_statement(self, ctx:Db2Parser.Create_transform_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tranform_list.
    def visitTranform_list(self, ctx:Db2Parser.Tranform_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tranform_list_item.
    def visitTranform_list_item(self, ctx:Db2Parser.Tranform_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#transform_group_list.
    def visitTransform_group_list(self, ctx:Db2Parser.Transform_group_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#transform_group_list_item.
    def visitTransform_group_list_item(self, ctx:Db2Parser.Transform_group_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_trigger_statement.
    def visitCreate_trigger_statement(self, ctx:Db2Parser.Create_trigger_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ref_list.
    def visitRef_list(self, ctx:Db2Parser.Ref_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ref_list_item.
    def visitRef_list_item(self, ctx:Db2Parser.Ref_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#old_new.
    def visitOld_new(self, ctx:Db2Parser.Old_newContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#correlation_name.
    def visitCorrelation_name(self, ctx:Db2Parser.Correlation_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#identifier.
    def visitIdentifier(self, ctx:Db2Parser.IdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#trigger_event.
    def visitTrigger_event(self, ctx:Db2Parser.Trigger_eventContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#triggered_action.
    def visitTriggered_action(self, ctx:Db2Parser.Triggered_actionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_procedure_statement.
    def visitSql_procedure_statement(self, ctx:Db2Parser.Sql_procedure_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_function_statement.
    def visitSql_function_statement(self, ctx:Db2Parser.Sql_function_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_trusted_context_statement.
    def visitCreate_trusted_context_statement(self, ctx:Db2Parser.Create_trusted_context_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#attr_list.
    def visitAttr_list(self, ctx:Db2Parser.Attr_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#attr_list_item.
    def visitAttr_list_item(self, ctx:Db2Parser.Attr_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#auth_list.
    def visitAuth_list(self, ctx:Db2Parser.Auth_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#auth_list_item.
    def visitAuth_list_item(self, ctx:Db2Parser.Auth_list_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#address_value.
    def visitAddress_value(self, ctx:Db2Parser.Address_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#encryption_value.
    def visitEncryption_value(self, ctx:Db2Parser.Encryption_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_type_statement.
    def visitCreate_type_statement(self, ctx:Db2Parser.Create_type_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_type_array_statement.
    def visitCreate_type_array_statement(self, ctx:Db2Parser.Create_type_array_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_type_cursor_statement.
    def visitCreate_type_cursor_statement(self, ctx:Db2Parser.Create_type_cursor_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_type_distinct_statement.
    def visitCreate_type_distinct_statement(self, ctx:Db2Parser.Create_type_distinct_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_type_row_statement.
    def visitCreate_type_row_statement(self, ctx:Db2Parser.Create_type_row_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#field_definition_list_paren.
    def visitField_definition_list_paren(self, ctx:Db2Parser.Field_definition_list_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#field_definition_list.
    def visitField_definition_list(self, ctx:Db2Parser.Field_definition_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#field_definition.
    def visitField_definition(self, ctx:Db2Parser.Field_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_type_structured_statement.
    def visitCreate_type_structured_statement(self, ctx:Db2Parser.Create_type_structured_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#structured_type_seq.
    def visitStructured_type_seq(self, ctx:Db2Parser.Structured_type_seqContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#attribute_definition_list_paren.
    def visitAttribute_definition_list_paren(self, ctx:Db2Parser.Attribute_definition_list_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#attribute_definition_list.
    def visitAttribute_definition_list(self, ctx:Db2Parser.Attribute_definition_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#attribute_definition.
    def visitAttribute_definition(self, ctx:Db2Parser.Attribute_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_specification_list.
    def visitMethod_specification_list(self, ctx:Db2Parser.Method_specification_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_specification.
    def visitMethod_specification(self, ctx:Db2Parser.Method_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_specification_seq.
    def visitMethod_specification_seq(self, ctx:Db2Parser.Method_specification_seqContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#as_locator.
    def visitAs_locator(self, ctx:Db2Parser.As_locatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#param_decl_list_paren.
    def visitParam_decl_list_paren(self, ctx:Db2Parser.Param_decl_list_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#param_decl_list.
    def visitParam_decl_list(self, ctx:Db2Parser.Param_decl_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#param_decl.
    def visitParam_decl(self, ctx:Db2Parser.Param_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_routine_characteristics.
    def visitSql_routine_characteristics(self, ctx:Db2Parser.Sql_routine_characteristicsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#external_routine_characteristics.
    def visitExternal_routine_characteristics(self, ctx:Db2Parser.External_routine_characteristicsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#length.
    def visitLength(self, ctx:Db2Parser.LengthContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#rep_type.
    def visitRep_type(self, ctx:Db2Parser.Rep_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#varchars.
    def visitVarchars(self, ctx:Db2Parser.VarcharsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#varbinaries.
    def visitVarbinaries(self, ctx:Db2Parser.VarbinariesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#for_bit_data.
    def visitFor_bit_data(self, ctx:Db2Parser.For_bit_dataContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#lob_options.
    def visitLob_options(self, ctx:Db2Parser.Lob_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_type_mapping_statement.
    def visitCreate_type_mapping_statement(self, ctx:Db2Parser.Create_type_mapping_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#for_bit_data_precision.
    def visitFor_bit_data_precision(self, ctx:Db2Parser.For_bit_data_precisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#precision.
    def visitPrecision(self, ctx:Db2Parser.PrecisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#scale.
    def visitScale(self, ctx:Db2Parser.ScaleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#precision_scale_comp.
    def visitPrecision_scale_comp(self, ctx:Db2Parser.Precision_scale_compContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#from_to.
    def visitFrom_to(self, ctx:Db2Parser.From_toContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_source_data_type.
    def visitData_source_data_type(self, ctx:Db2Parser.Data_source_data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#local_data_type.
    def visitLocal_data_type(self, ctx:Db2Parser.Local_data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#remote_server.
    def visitRemote_server(self, ctx:Db2Parser.Remote_serverContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#server_version.
    def visitServer_version(self, ctx:Db2Parser.Server_versionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#server_type.
    def visitServer_type(self, ctx:Db2Parser.Server_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#version.
    def visitVersion(self, ctx:Db2Parser.VersionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#release.
    def visitRelease(self, ctx:Db2Parser.ReleaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#mod.
    def visitMod(self, ctx:Db2Parser.ModContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_usage_list_statement.
    def visitCreate_usage_list_statement(self, ctx:Db2Parser.Create_usage_list_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_user_mapping_statement.
    def visitCreate_user_mapping_statement(self, ctx:Db2Parser.Create_user_mapping_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#user_mapping_options_paren.
    def visitUser_mapping_options_paren(self, ctx:Db2Parser.User_mapping_options_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#user_mapping_options.
    def visitUser_mapping_options(self, ctx:Db2Parser.User_mapping_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_variable_statement.
    def visitCreate_variable_statement(self, ctx:Db2Parser.Create_variable_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#constant_.
    def visitConstant_(self, ctx:Db2Parser.Constant_Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#special_register.
    def visitSpecial_register(self, ctx:Db2Parser.Special_registerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#global_variable.
    def visitGlobal_variable(self, ctx:Db2Parser.Global_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_type_1.
    def visitData_type_1(self, ctx:Db2Parser.Data_type_1Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#cursor_value_constructor.
    def visitCursor_value_constructor(self, ctx:Db2Parser.Cursor_value_constructorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#anchored_variable_data_type.
    def visitAnchored_variable_data_type(self, ctx:Db2Parser.Anchored_variable_data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#holdability.
    def visitHoldability(self, ctx:Db2Parser.HoldabilityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#returnability.
    def visitReturnability(self, ctx:Db2Parser.ReturnabilityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_view_statement.
    def visitCreate_view_statement(self, ctx:Db2Parser.Create_view_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_view_seq.
    def visitCreate_view_seq(self, ctx:Db2Parser.Create_view_seqContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#fullselect.
    def visitFullselect(self, ctx:Db2Parser.FullselectContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#subselect.
    def visitSubselect(self, ctx:Db2Parser.SubselectContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#select_clause.
    def visitSelect_clause(self, ctx:Db2Parser.Select_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#select_clause_item.
    def visitSelect_clause_item(self, ctx:Db2Parser.Select_clause_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#from_clause.
    def visitFrom_clause(self, ctx:Db2Parser.From_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_reference.
    def visitTable_reference(self, ctx:Db2Parser.Table_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_reference_list.
    def visitTable_reference_list(self, ctx:Db2Parser.Table_reference_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#singles_table_reference.
    def visitSingles_table_reference(self, ctx:Db2Parser.Singles_table_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#period_specification.
    def visitPeriod_specification(self, ctx:Db2Parser.Period_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#value.
    def visitValue(self, ctx:Db2Parser.ValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#correlation_clause.
    def visitCorrelation_clause(self, ctx:Db2Parser.Correlation_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tablesample_clause.
    def visitTablesample_clause(self, ctx:Db2Parser.Tablesample_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#numeric_expression.
    def visitNumeric_expression(self, ctx:Db2Parser.Numeric_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#single_view_reference.
    def visitSingle_view_reference(self, ctx:Db2Parser.Single_view_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#single_nickname_reference.
    def visitSingle_nickname_reference(self, ctx:Db2Parser.Single_nickname_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#only_table_reference.
    def visitOnly_table_reference(self, ctx:Db2Parser.Only_table_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#outer_table_reference.
    def visitOuter_table_reference(self, ctx:Db2Parser.Outer_table_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#analyze_table_reference.
    def visitAnalyze_table_reference(self, ctx:Db2Parser.Analyze_table_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#implementation_clause.
    def visitImplementation_clause(self, ctx:Db2Parser.Implementation_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#nested_table_reference.
    def visitNested_table_reference(self, ctx:Db2Parser.Nested_table_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#continue_handler.
    def visitContinue_handler(self, ctx:Db2Parser.Continue_handlerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#specific_condition_value.
    def visitSpecific_condition_value(self, ctx:Db2Parser.Specific_condition_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_change_table_reference.
    def visitData_change_table_reference(self, ctx:Db2Parser.Data_change_table_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#searched_update_statement.
    def visitSearched_update_statement(self, ctx:Db2Parser.Searched_update_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#searched_delete_statement.
    def visitSearched_delete_statement(self, ctx:Db2Parser.Searched_delete_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#final_new.
    def visitFinal_new(self, ctx:Db2Parser.Final_newContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#final_new_old.
    def visitFinal_new_old(self, ctx:Db2Parser.Final_new_oldContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_function_reference.
    def visitTable_function_reference(self, ctx:Db2Parser.Table_function_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_udf_cardinality_clause.
    def visitTable_udf_cardinality_clause(self, ctx:Db2Parser.Table_udf_cardinality_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#typed_correlation_clause.
    def visitTyped_correlation_clause(self, ctx:Db2Parser.Typed_correlation_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_name_data_type.
    def visitColumn_name_data_type(self, ctx:Db2Parser.Column_name_data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#collection_derived_table.
    def visitCollection_derived_table(self, ctx:Db2Parser.Collection_derived_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_function.
    def visitTable_function(self, ctx:Db2Parser.Table_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#xmltable_expression.
    def visitXmltable_expression(self, ctx:Db2Parser.Xmltable_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#xmltable_function.
    def visitXmltable_function(self, ctx:Db2Parser.Xmltable_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#joined_table.
    def visitJoined_table(self, ctx:Db2Parser.Joined_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#join_condition.
    def visitJoin_condition(self, ctx:Db2Parser.Join_conditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#outer.
    def visitOuter(self, ctx:Db2Parser.OuterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#external_table_reference.
    def visitExternal_table_reference(self, ctx:Db2Parser.External_table_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_definition_2.
    def visitColumn_definition_2(self, ctx:Db2Parser.Column_definition_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#file_name.
    def visitFile_name(self, ctx:Db2Parser.File_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#where_clause.
    def visitWhere_clause(self, ctx:Db2Parser.Where_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#group_by_clause.
    def visitGroup_by_clause(self, ctx:Db2Parser.Group_by_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#group_by_clause_opts.
    def visitGroup_by_clause_opts(self, ctx:Db2Parser.Group_by_clause_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grouping_expression.
    def visitGrouping_expression(self, ctx:Db2Parser.Grouping_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grouping_sets.
    def visitGrouping_sets(self, ctx:Db2Parser.Grouping_setsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#super_groups.
    def visitSuper_groups(self, ctx:Db2Parser.Super_groupsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#grant_total.
    def visitGrant_total(self, ctx:Db2Parser.Grant_totalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#having_clause.
    def visitHaving_clause(self, ctx:Db2Parser.Having_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#order_by_clause.
    def visitOrder_by_clause(self, ctx:Db2Parser.Order_by_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#order_by_clause_opts.
    def visitOrder_by_clause_opts(self, ctx:Db2Parser.Order_by_clause_optsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_designator.
    def visitTable_designator(self, ctx:Db2Parser.Table_designatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#asc_desc.
    def visitAsc_desc(self, ctx:Db2Parser.Asc_descContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#first_last.
    def visitFirst_last(self, ctx:Db2Parser.First_lastContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sort_key.
    def visitSort_key(self, ctx:Db2Parser.Sort_keyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#simple_column_name.
    def visitSimple_column_name(self, ctx:Db2Parser.Simple_column_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#simple_integer.
    def visitSimple_integer(self, ctx:Db2Parser.Simple_integerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sork_key_expression.
    def visitSork_key_expression(self, ctx:Db2Parser.Sork_key_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#offset_clause.
    def visitOffset_clause(self, ctx:Db2Parser.Offset_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#offset_row_count.
    def visitOffset_row_count(self, ctx:Db2Parser.Offset_row_countContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#fetch_clause.
    def visitFetch_clause(self, ctx:Db2Parser.Fetch_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#fetch_row_count.
    def visitFetch_row_count(self, ctx:Db2Parser.Fetch_row_countContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_rows.
    def visitRow_rows(self, ctx:Db2Parser.Row_rowsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#isolation_clause.
    def visitIsolation_clause(self, ctx:Db2Parser.Isolation_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#lock_request_clause.
    def visitLock_request_clause(self, ctx:Db2Parser.Lock_request_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#values_clause.
    def visitValues_clause(self, ctx:Db2Parser.Values_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#values_row.
    def visitValues_row(self, ctx:Db2Parser.Values_rowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#root_view_definition.
    def visitRoot_view_definition(self, ctx:Db2Parser.Root_view_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#subview_definition.
    def visitSubview_definition(self, ctx:Db2Parser.Subview_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#oid_column.
    def visitOid_column(self, ctx:Db2Parser.Oid_columnContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#with_options.
    def visitWith_options(self, ctx:Db2Parser.With_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#with_option_def.
    def visitWith_option_def(self, ctx:Db2Parser.With_option_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#with_option_scope_def.
    def visitWith_option_scope_def(self, ctx:Db2Parser.With_option_scope_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#under_clause.
    def visitUnder_clause(self, ctx:Db2Parser.Under_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_work_action_set_statement.
    def visitCreate_work_action_set_statement(self, ctx:Db2Parser.Create_work_action_set_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_action_definition_list_paren.
    def visitWork_action_definition_list_paren(self, ctx:Db2Parser.Work_action_definition_list_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_action_definition_list.
    def visitWork_action_definition_list(self, ctx:Db2Parser.Work_action_definition_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_action_definition.
    def visitWork_action_definition(self, ctx:Db2Parser.Work_action_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#action_types_clause.
    def visitAction_types_clause(self, ctx:Db2Parser.Action_types_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#threshold_types_clause.
    def visitThreshold_types_clause(self, ctx:Db2Parser.Threshold_types_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#second_seconds.
    def visitSecond_seconds(self, ctx:Db2Parser.Second_secondsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#hours_minutes.
    def visitHours_minutes(self, ctx:Db2Parser.Hours_minutesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#threshold_exceeded_actions.
    def visitThreshold_exceeded_actions(self, ctx:Db2Parser.Threshold_exceeded_actionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#collect_activity_data_clause.
    def visitCollect_activity_data_clause(self, ctx:Db2Parser.Collect_activity_data_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#with_without.
    def visitWith_without(self, ctx:Db2Parser.With_withoutContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#histogram_templace_clause.
    def visitHistogram_templace_clause(self, ctx:Db2Parser.Histogram_templace_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_work_class_set_statement.
    def visitCreate_work_class_set_statement(self, ctx:Db2Parser.Create_work_class_set_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_class_definition_list_paren.
    def visitWork_class_definition_list_paren(self, ctx:Db2Parser.Work_class_definition_list_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_class_definition_list.
    def visitWork_class_definition_list(self, ctx:Db2Parser.Work_class_definition_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_class_definition.
    def visitWork_class_definition(self, ctx:Db2Parser.Work_class_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_attributes.
    def visitWork_attributes(self, ctx:Db2Parser.Work_attributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#position_clause.
    def visitPosition_clause(self, ctx:Db2Parser.Position_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#position_.
    def visitPosition_(self, ctx:Db2Parser.Position_Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#for_from_to_clause.
    def visitFor_from_to_clause(self, ctx:Db2Parser.For_from_to_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#from_value.
    def visitFrom_value(self, ctx:Db2Parser.From_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#to_value.
    def visitTo_value(self, ctx:Db2Parser.To_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_tag_clause.
    def visitData_tag_clause(self, ctx:Db2Parser.Data_tag_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#schema_clause.
    def visitSchema_clause(self, ctx:Db2Parser.Schema_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_workload_statement.
    def visitCreate_workload_statement(self, ctx:Db2Parser.Create_workload_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#pkg_exec_seq.
    def visitPkg_exec_seq(self, ctx:Db2Parser.Pkg_exec_seqContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#position_clause_2.
    def visitPosition_clause_2(self, ctx:Db2Parser.Position_clause_2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#connection_attributes.
    def visitConnection_attributes(self, ctx:Db2Parser.Connection_attributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#string_list.
    def visitString_list(self, ctx:Db2Parser.String_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#string_list_paren.
    def visitString_list_paren(self, ctx:Db2Parser.String_list_parenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#workload_attributes.
    def visitWorkload_attributes(self, ctx:Db2Parser.Workload_attributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#degree.
    def visitDegree(self, ctx:Db2Parser.DegreeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#allow_disallow.
    def visitAllow_disallow(self, ctx:Db2Parser.Allow_disallowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#collect_on_clause.
    def visitCollect_on_clause(self, ctx:Db2Parser.Collect_on_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#collect_details_clause.
    def visitCollect_details_clause(self, ctx:Db2Parser.Collect_details_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#collect_lock_wait_options.
    def visitCollect_lock_wait_options(self, ctx:Db2Parser.Collect_lock_wait_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#wait_time.
    def visitWait_time(self, ctx:Db2Parser.Wait_timeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#create_wrapper_statement.
    def visitCreate_wrapper_statement(self, ctx:Db2Parser.Create_wrapper_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#wrapper_option_list.
    def visitWrapper_option_list(self, ctx:Db2Parser.Wrapper_option_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#wrapper_option.
    def visitWrapper_option(self, ctx:Db2Parser.Wrapper_optionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#expression.
    def visitExpression(self, ctx:Db2Parser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#function_invocation.
    def visitFunction_invocation(self, ctx:Db2Parser.Function_invocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#all_distinct.
    def visitAll_distinct(self, ctx:Db2Parser.All_distinctContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#scalar_fullselect.
    def visitScalar_fullselect(self, ctx:Db2Parser.Scalar_fullselectContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#cast_specification.
    def visitCast_specification(self, ctx:Db2Parser.Cast_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#cursor_cast_specification.
    def visitCursor_cast_specification(self, ctx:Db2Parser.Cursor_cast_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_cast_specification.
    def visitRow_cast_specification(self, ctx:Db2Parser.Row_cast_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#interval_cast_specification.
    def visitInterval_cast_specification(self, ctx:Db2Parser.Interval_cast_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#xmlcast_specification.
    def visitXmlcast_specification(self, ctx:Db2Parser.Xmlcast_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#array_element_specification.
    def visitArray_element_specification(self, ctx:Db2Parser.Array_element_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#array_constructor.
    def visitArray_constructor(self, ctx:Db2Parser.Array_constructorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_invocation.
    def visitMethod_invocation(self, ctx:Db2Parser.Method_invocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#olap_specification.
    def visitOlap_specification(self, ctx:Db2Parser.Olap_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ordered_olap_specification.
    def visitOrdered_olap_specification(self, ctx:Db2Parser.Ordered_olap_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#window_partition_clause.
    def visitWindow_partition_clause(self, ctx:Db2Parser.Window_partition_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#window_order_clause.
    def visitWindow_order_clause(self, ctx:Db2Parser.Window_order_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#numbering_specification.
    def visitNumbering_specification(self, ctx:Db2Parser.Numbering_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#aggregation_specification.
    def visitAggregation_specification(self, ctx:Db2Parser.Aggregation_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#olap_aggregate_function.
    def visitOlap_aggregate_function(self, ctx:Db2Parser.Olap_aggregate_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#first_value_function.
    def visitFirst_value_function(self, ctx:Db2Parser.First_value_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#last_value_function.
    def visitLast_value_function(self, ctx:Db2Parser.Last_value_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#nth_value_function.
    def visitNth_value_function(self, ctx:Db2Parser.Nth_value_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ratio_to_report_function.
    def visitRatio_to_report_function(self, ctx:Db2Parser.Ratio_to_report_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#ignore_respect_nulls.
    def visitIgnore_respect_nulls(self, ctx:Db2Parser.Ignore_respect_nullsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#from_first_last.
    def visitFrom_first_last(self, ctx:Db2Parser.From_first_lastContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#window_aggregation_group_clause.
    def visitWindow_aggregation_group_clause(self, ctx:Db2Parser.Window_aggregation_group_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#group_start.
    def visitGroup_start(self, ctx:Db2Parser.Group_startContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#group_between.
    def visitGroup_between(self, ctx:Db2Parser.Group_betweenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#group_bound1.
    def visitGroup_bound1(self, ctx:Db2Parser.Group_bound1Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#group_bound2.
    def visitGroup_bound2(self, ctx:Db2Parser.Group_bound2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#group_end.
    def visitGroup_end(self, ctx:Db2Parser.Group_endContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_change_expression.
    def visitRow_change_expression(self, ctx:Db2Parser.Row_change_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sequence_reference.
    def visitSequence_reference(self, ctx:Db2Parser.Sequence_referenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#subtype_treatment.
    def visitSubtype_treatment(self, ctx:Db2Parser.Subtype_treatmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#expression_list.
    def visitExpression_list(self, ctx:Db2Parser.Expression_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#expression_list_in_parentheses.
    def visitExpression_list_in_parentheses(self, ctx:Db2Parser.Expression_list_in_parenthesesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#id_.
    def visitId_(self, ctx:Db2Parser.Id_Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#exposed_name.
    def visitExposed_name(self, ctx:Db2Parser.Exposed_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#name.
    def visitName(self, ctx:Db2Parser.NameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#label.
    def visitLabel(self, ctx:Db2Parser.LabelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#host_label.
    def visitHost_label(self, ctx:Db2Parser.Host_labelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#library_name.
    def visitLibrary_name(self, ctx:Db2Parser.Library_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#array_type_name.
    def visitArray_type_name(self, ctx:Db2Parser.Array_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#attribute_name.
    def visitAttribute_name(self, ctx:Db2Parser.Attribute_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_type_name.
    def visitRow_type_name(self, ctx:Db2Parser.Row_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#authorization_name.
    def visitAuthorization_name(self, ctx:Db2Parser.Authorization_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#boolean_variable_name.
    def visitBoolean_variable_name(self, ctx:Db2Parser.Boolean_variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#array_variable_name.
    def visitArray_variable_name(self, ctx:Db2Parser.Array_variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#column_name.
    def visitColumn_name(self, ctx:Db2Parser.Column_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#constraint_name.
    def visitConstraint_name(self, ctx:Db2Parser.Constraint_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#descriptor_name.
    def visitDescriptor_name(self, ctx:Db2Parser.Descriptor_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#distinct_type_name.
    def visitDistinct_type_name(self, ctx:Db2Parser.Distinct_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#cursor_name.
    def visitCursor_name(self, ctx:Db2Parser.Cursor_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#cursor_type_name.
    def visitCursor_type_name(self, ctx:Db2Parser.Cursor_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#condition_name.
    def visitCondition_name(self, ctx:Db2Parser.Condition_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#data_source_name.
    def visitData_source_name(self, ctx:Db2Parser.Data_source_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#expression_name.
    def visitExpression_name(self, ctx:Db2Parser.Expression_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#group_name.
    def visitGroup_name(self, ctx:Db2Parser.Group_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#policy_name.
    def visitPolicy_name(self, ctx:Db2Parser.Policy_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#bufferpool_name.
    def visitBufferpool_name(self, ctx:Db2Parser.Bufferpool_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_partition_name.
    def visitDb_partition_name(self, ctx:Db2Parser.Db_partition_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#database_name.
    def visitDatabase_name(self, ctx:Db2Parser.Database_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#event_monitor_name.
    def visitEvent_monitor_name(self, ctx:Db2Parser.Event_monitor_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#field_name.
    def visitField_name(self, ctx:Db2Parser.Field_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#for_loop_name.
    def visitFor_loop_name(self, ctx:Db2Parser.For_loop_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#function_name.
    def visitFunction_name(self, ctx:Db2Parser.Function_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#function_mapping_name.
    def visitFunction_mapping_name(self, ctx:Db2Parser.Function_mapping_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#global_variable_name.
    def visitGlobal_variable_name(self, ctx:Db2Parser.Global_variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#hierarchy_name.
    def visitHierarchy_name(self, ctx:Db2Parser.Hierarchy_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#host_variable_name.
    def visitHost_variable_name(self, ctx:Db2Parser.Host_variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#parameter_marker.
    def visitParameter_marker(self, ctx:Db2Parser.Parameter_markerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#template_name.
    def visitTemplate_name(self, ctx:Db2Parser.Template_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#index_name.
    def visitIndex_name(self, ctx:Db2Parser.Index_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#index_extension_name.
    def visitIndex_extension_name(self, ctx:Db2Parser.Index_extension_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#input_descriptor_name.
    def visitInput_descriptor_name(self, ctx:Db2Parser.Input_descriptor_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#mask_name.
    def visitMask_name(self, ctx:Db2Parser.Mask_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#method_name.
    def visitMethod_name(self, ctx:Db2Parser.Method_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#model_name.
    def visitModel_name(self, ctx:Db2Parser.Model_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#module_name.
    def visitModule_name(self, ctx:Db2Parser.Module_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#new_owner.
    def visitNew_owner(self, ctx:Db2Parser.New_ownerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#nick_name.
    def visitNick_name(self, ctx:Db2Parser.Nick_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#object_name.
    def visitObject_name(self, ctx:Db2Parser.Object_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#oid_column_name.
    def visitOid_column_name(self, ctx:Db2Parser.Oid_column_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#optimization_profile_name.
    def visitOptimization_profile_name(self, ctx:Db2Parser.Optimization_profile_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#package_name.
    def visitPackage_name(self, ctx:Db2Parser.Package_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#partition_name.
    def visitPartition_name(self, ctx:Db2Parser.Partition_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#path_name.
    def visitPath_name(self, ctx:Db2Parser.Path_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#permission_name.
    def visitPermission_name(self, ctx:Db2Parser.Permission_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#pipe_name.
    def visitPipe_name(self, ctx:Db2Parser.Pipe_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#procedure_name.
    def visitProcedure_name(self, ctx:Db2Parser.Procedure_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#result_descriptor_name.
    def visitResult_descriptor_name(self, ctx:Db2Parser.Result_descriptor_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#role_name.
    def visitRole_name(self, ctx:Db2Parser.Role_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#root_table_name.
    def visitRoot_table_name(self, ctx:Db2Parser.Root_table_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#root_view_name.
    def visitRoot_view_name(self, ctx:Db2Parser.Root_view_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#row_variable_name.
    def visitRow_variable_name(self, ctx:Db2Parser.Row_variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_schema_name.
    def visitSource_schema_name(self, ctx:Db2Parser.Source_schema_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_package_name.
    def visitSource_package_name(self, ctx:Db2Parser.Source_package_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_procedure_name.
    def visitSource_procedure_name(self, ctx:Db2Parser.Source_procedure_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_parameter_name.
    def visitSql_parameter_name(self, ctx:Db2Parser.Sql_parameter_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sql_variable_name.
    def visitSql_variable_name(self, ctx:Db2Parser.Sql_variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#transition_variable_name.
    def visitTransition_variable_name(self, ctx:Db2Parser.Transition_variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#savepoint_name.
    def visitSavepoint_name(self, ctx:Db2Parser.Savepoint_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#specific_name.
    def visitSpecific_name(self, ctx:Db2Parser.Specific_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#schema.
    def visitSchema(self, ctx:Db2Parser.SchemaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#schema_name.
    def visitSchema_name(self, ctx:Db2Parser.Schema_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#search_method_name.
    def visitSearch_method_name(self, ctx:Db2Parser.Search_method_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#server_name.
    def visitServer_name(self, ctx:Db2Parser.Server_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#server_option_name.
    def visitServer_option_name(self, ctx:Db2Parser.Server_option_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#session_authorization_name.
    def visitSession_authorization_name(self, ctx:Db2Parser.Session_authorization_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#component_name.
    def visitComponent_name(self, ctx:Db2Parser.Component_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sec_label_comp_name.
    def visitSec_label_comp_name(self, ctx:Db2Parser.Sec_label_comp_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#security_policy_name.
    def visitSecurity_policy_name(self, ctx:Db2Parser.Security_policy_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#security_label_name.
    def visitSecurity_label_name(self, ctx:Db2Parser.Security_label_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#sequence_name.
    def visitSequence_name(self, ctx:Db2Parser.Sequence_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#service_class_name.
    def visitService_class_name(self, ctx:Db2Parser.Service_class_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#service_superclass_name.
    def visitService_superclass_name(self, ctx:Db2Parser.Service_superclass_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#storagegroup_name.
    def visitStoragegroup_name(self, ctx:Db2Parser.Storagegroup_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#supertype_name.
    def visitSupertype_name(self, ctx:Db2Parser.Supertype_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#superview_name.
    def visitSuperview_name(self, ctx:Db2Parser.Superview_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#service_subclass_name.
    def visitService_subclass_name(self, ctx:Db2Parser.Service_subclass_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#statement_name.
    def visitStatement_name(self, ctx:Db2Parser.Statement_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#table_name.
    def visitTable_name(self, ctx:Db2Parser.Table_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#tablespace_name.
    def visitTablespace_name(self, ctx:Db2Parser.Tablespace_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#target_identifier.
    def visitTarget_identifier(self, ctx:Db2Parser.Target_identifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#threshold_name.
    def visitThreshold_name(self, ctx:Db2Parser.Threshold_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#trigger_name.
    def visitTrigger_name(self, ctx:Db2Parser.Trigger_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#context_name.
    def visitContext_name(self, ctx:Db2Parser.Context_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#usage_list_name.
    def visitUsage_list_name(self, ctx:Db2Parser.Usage_list_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#type_name.
    def visitType_name(self, ctx:Db2Parser.Type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#type_mapping_name.
    def visitType_mapping_name(self, ctx:Db2Parser.Type_mapping_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#typed_table_name.
    def visitTyped_table_name(self, ctx:Db2Parser.Typed_table_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#typed_view_name.
    def visitTyped_view_name(self, ctx:Db2Parser.Typed_view_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#user_mapping_option_name.
    def visitUser_mapping_option_name(self, ctx:Db2Parser.User_mapping_option_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#view_name.
    def visitView_name(self, ctx:Db2Parser.View_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#variable_name.
    def visitVariable_name(self, ctx:Db2Parser.Variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_action_set_name.
    def visitWork_action_set_name(self, ctx:Db2Parser.Work_action_set_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_class_set_name.
    def visitWork_class_set_name(self, ctx:Db2Parser.Work_class_set_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#workload_name.
    def visitWorkload_name(self, ctx:Db2Parser.Workload_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_action_name.
    def visitWork_action_name(self, ctx:Db2Parser.Work_action_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#work_class_name.
    def visitWork_class_name(self, ctx:Db2Parser.Work_class_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#wrapper_name.
    def visitWrapper_name(self, ctx:Db2Parser.Wrapper_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#wrapper_option_name.
    def visitWrapper_option_name(self, ctx:Db2Parser.Wrapper_option_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#xsrobject_name.
    def visitXsrobject_name(self, ctx:Db2Parser.Xsrobject_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#parameter_name.
    def visitParameter_name(self, ctx:Db2Parser.Parameter_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#cursor_variable_name.
    def visitCursor_variable_name(self, ctx:Db2Parser.Cursor_variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#alias_name.
    def visitAlias_name(self, ctx:Db2Parser.Alias_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#db_partition_group_name.
    def visitDb_partition_group_name(self, ctx:Db2Parser.Db_partition_group_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_index_name.
    def visitSource_index_name(self, ctx:Db2Parser.Source_index_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_table_name.
    def visitSource_table_name(self, ctx:Db2Parser.Source_table_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_storagegroup_name.
    def visitSource_storagegroup_name(self, ctx:Db2Parser.Source_storagegroup_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#target_storagegroup_name.
    def visitTarget_storagegroup_name(self, ctx:Db2Parser.Target_storagegroup_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#source_tablespace_name.
    def visitSource_tablespace_name(self, ctx:Db2Parser.Source_tablespace_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#target_tablespace_name.
    def visitTarget_tablespace_name(self, ctx:Db2Parser.Target_tablespace_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#unqualified_function_name.
    def visitUnqualified_function_name(self, ctx:Db2Parser.Unqualified_function_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#unqualified_procedure_name.
    def visitUnqualified_procedure_name(self, ctx:Db2Parser.Unqualified_procedure_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#unqualified_specific_name.
    def visitUnqualified_specific_name(self, ctx:Db2Parser.Unqualified_specific_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#period_name.
    def visitPeriod_name(self, ctx:Db2Parser.Period_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#history_table_name.
    def visitHistory_table_name(self, ctx:Db2Parser.History_table_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#xml_schema_name.
    def visitXml_schema_name(self, ctx:Db2Parser.Xml_schema_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by Db2Parser#todo.
    def visitTodo(self, ctx:Db2Parser.TodoContext):
        return self.visitChildren(ctx)



del Db2Parser